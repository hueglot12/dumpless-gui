
import asyncio
import html
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote_plus


ROOT_DIR = Path(__file__).resolve().parent
HTML_DIR = ROOT_DIR / "htmls"
EMAIL_HTML_TEMPLATE = HTML_DIR / "email_report.html"
EMAIL_CSS_NAME = "email_report.css"


def _favicon_by_domain(domain: str) -> str:
    domain = (domain or "").strip().lower()
    if not domain:
        return "https://www.google.com/s2/favicons?domain=example.com&sz=64"
    return f"https://www.google.com/s2/favicons?domain={quote_plus(domain)}&sz=64"


def _logo_for_email(email_value: str) -> str:
    provider = email_value.split("@", 1)[1].strip().lower() if "@" in email_value else "unknown"
    return _favicon_by_domain(provider)


def _logo_for_site(site_domain: str) -> str:
    return _favicon_by_domain(site_domain)


def _service_domain_from_name(name: str) -> str:
    raw = (name or "").strip().lower()
    mapping = {
        "adobe": "adobe.com",
        "duolingo": "duolingo.com",
        "github": "github.com",
        "discord": "discord.com",
        "evernote": "evernote.com",
        "pinterest": "pinterest.com",
        "soundcloud": "soundcloud.com",
        "snapchat": "snapchat.com",
        "replit": "replit.com",
        "zoho": "zoho.com",
    }
    if raw in mapping:
        return mapping[raw]
    raw = re.sub(r"[^a-z0-9._-]+", "", raw)
    if "." in raw:
        return raw
    return f"{raw}.com" if raw else "unknown"


async def _run_cmd(*args: str, cwd: str | None = None, timeout: int = 180) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *args,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return 124, "TIMEOUT"
    return proc.returncode, stdout.decode("utf-8", errors="replace")


def _normalize_username(email_value: str) -> str:
    return email_value.split("@", 1)[0].strip()


def _clean_provider(name: str) -> str:
    value = re.sub(r"\s+", " ", (name or "").strip())
    return value.rstrip(":").strip()


def parse_mailcat_output(output: str) -> list[dict]:
    results: list[dict] = []
    current_provider = None
    seen = set()

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.endswith(":") and not line.startswith("*"):
            provider = _clean_provider(line)
            if provider.lower() not in {"traceback", "runtimewarning"}:
                current_provider = provider
            continue

        if line.startswith("*"):
            email_match = re.search(r'([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})', line, re.I)
            if not email_match:
                continue

            email_value = email_match.group(1).lower()
            provider_domain = email_value.split("@", 1)[1].lower()
            provider_name = current_provider or provider_domain

            key = ("mailcat", email_value, provider_name.lower())
            if key in seen:
                continue
            seen.add(key)

            results.append({
                "source": "mailcat",
                "label": provider_name,
                "email": email_value,
                "domain": provider_domain,
                "status": "alias",
                "logo": _logo_for_email(email_value),
            })

    return results


def parse_holehe_output(output: str) -> dict:
    found = []
    errors = []
    checked = 0
    seen = set()

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        summary_match = re.search(r'(\d+)\s+websites checked', line, re.I)
        if summary_match:
            checked = int(summary_match.group(1))

        service_match = re.match(r'^\[([\+\-\!x])\]\s+(.+?)$', line)
        if not service_match:
            continue

        status_symbol = service_match.group(1)
        site = service_match.group(2).strip()
        site_domain = site.lower()

        if status_symbol == '+':
            key = ("holehe", site_domain)
            if key in seen:
                continue
            seen.add(key)
            found.append({
                "source": "holehe",
                "label": site_domain,
                "email": "",
                "domain": site_domain,
                "status": "found",
                "logo": _logo_for_site(site_domain),
            })
        elif status_symbol == '!':
            errors.append(site_domain)

    return {
        "checked": checked,
        "found": found,
        "errors": errors,
    }


def parse_blackbird_output(output: str) -> dict:
    found = []
    checked = 0
    duration = ""
    seen = set()

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        summary_match = re.search(r'Check completed in\s+([0-9.]+\s+seconds)\s+\((\d+)\s+sites\)', line, re.I)
        if summary_match:
            duration = summary_match.group(1)
            checked = int(summary_match.group(2))

        service_match = re.search(r'✔️\s+\[([^\]]+)\]\s+(https?://\S+)', line)
        if service_match:
            service_name = service_match.group(1).strip()
            service_url = service_match.group(2).strip()
            domain_match = re.search(r'https?://([^/\s]+)', service_url)
            service_domain = domain_match.group(1).lower() if domain_match else _service_domain_from_name(service_name)

            key = ("blackbird", service_domain)
            if key in seen:
                continue
            seen.add(key)

            found.append({
                "source": "blackbird",
                "label": service_name,
                "email": "",
                "domain": service_domain,
                "status": "found",
                "url": service_url,
                "logo": _logo_for_site(service_domain),
            })

    return {
        "checked": checked,
        "duration": duration,
        "found": found,
    }


def _metric_card(title: str, value: str, subtitle: str = "") -> str:
    subtitle_html = f'<div class="metric-sub">{html.escape(subtitle)}</div>' if subtitle else ""
    return (
        '<div class="metric">'
        f'<div class="metric-title">{html.escape(title)}</div>'
        f'<div class="metric-value">{html.escape(value)}</div>'
        f'{subtitle_html}'
        '</div>'
    )


def _build_email_row(item: dict) -> str:
    provider = item.get("label") or item.get("domain") or "Unknown"
    email_value = item.get("email") or "—"
    domain = item.get("domain") or "unknown"
    logo = item.get("logo") or _logo_for_site(domain)

    return f"""
    <div class="result-row">
        <div class="result-main">
            <img class="result-logo" src="{html.escape(logo)}" alt="{html.escape(provider)}">
            <div class="result-text">
                <div class="result-title">{html.escape(email_value)}</div>
                <div class="result-subtitle">{html.escape(provider)}</div>
            </div>
        </div>
        <div class="result-domain">{html.escape(domain)}</div>
    </div>
    """


def _build_site_row(item: dict) -> str:
    title = item.get("label") or item.get("domain") or "Unknown"
    domain = item.get("domain") or "unknown"
    logo = item.get("logo") or _logo_for_site(domain)
    url = item.get("url", "")
    url_html = f'<a class="result-link" href="{html.escape(url)}" target="_blank">{html.escape(domain)}</a>' if url else html.escape(domain)

    return f"""
    <div class="result-row">
        <div class="result-main">
            <img class="result-logo" src="{html.escape(logo)}" alt="{html.escape(title)}">
            <div class="result-text">
                <div class="result-title">{html.escape(title)}</div>
                <div class="result-subtitle">Аккаунт/след найден</div>
            </div>
        </div>
        <div class="result-domain">{url_html}</div>
    </div>
    """


def _build_notice_list(items: list[str], empty_text: str) -> str:
    if not items:
        return f'<div class="empty-block">{html.escape(empty_text)}</div>'

    rows = ''.join(f'<li>{html.escape(x)}</li>' for x in items)
    return f'<ul class="simple-list">{rows}</ul>'


def _load_template() -> str:
    with open(EMAIL_HTML_TEMPLATE, "r", encoding="utf-8") as f:
        return f.read()


async def run_email_osint(
    email_value: str,
    *,
    holehe_cmd: list[str] | None = None,
    mailcat_cmd: list[str] | None = None,
    blackbird_cmd: list[str] | None = None,
    holehe_cwd: str | None = None,
    mailcat_cwd: str | None = None,
    blackbird_cwd: str | None = None,
) -> dict:
    email_value = email_value.strip().lower()
    if not email_value or "@" not in email_value:
        raise ValueError("Нужен корректный email")

    username = _normalize_username(email_value)

    holehe_cmd = holehe_cmd or ["holehe", email_value]
    mailcat_cmd = mailcat_cmd or ["python", "mailcat.py", username]
    blackbird_cmd = blackbird_cmd or ["python", "blackbird.py", "-e", email_value]

    tasks = [
        _run_cmd(*holehe_cmd, cwd=holehe_cwd, timeout=220),
        _run_cmd(*mailcat_cmd, cwd=mailcat_cwd, timeout=220),
        _run_cmd(*blackbird_cmd, cwd=blackbird_cwd, timeout=220),
    ]

    holehe_res, mailcat_res, blackbird_res = await asyncio.gather(*tasks, return_exceptions=False)

    holehe_code, holehe_output = holehe_res
    mailcat_code, mailcat_output = mailcat_res
    blackbird_code, blackbird_output = blackbird_res

    mailcat_items = parse_mailcat_output(mailcat_output) if mailcat_output else []
    holehe_info = parse_holehe_output(holehe_output) if holehe_output else {"checked": 0, "found": [], "errors": []}
    blackbird_info = parse_blackbird_output(blackbird_output) if blackbird_output else {"checked": 0, "duration": "", "found": []}

    return {
        "target_email": email_value,
        "username": username,
        "mailcat": {
            "return_code": mailcat_code,
            "items": mailcat_items,
            "raw": mailcat_output,
        },
        "holehe": {
            "return_code": holehe_code,
            **holehe_info,
            "raw": holehe_output,
        },
        "blackbird": {
            "return_code": blackbird_code,
            **blackbird_info,
            "raw": blackbird_output,
        },
    }


def build_email_report_html(
    data: dict,
    *,
    css_url: str = "http://127.0.0.1:5000/email_report.css",
    output_path: str | None = None,
) -> str:
    target_email = data["target_email"]
    username = data["username"]

    mailcat_items = data["mailcat"]["items"]
    holehe_items = data["holehe"]["found"]
    blackbird_items = data["blackbird"]["found"]

    unique_site_domains = sorted({x["domain"] for x in (holehe_items + blackbird_items)})
    total_hits = len(mailcat_items) + len(unique_site_domains)

    metrics_html = (
        _metric_card("Цель", target_email, f"Логин: {username}") +
        _metric_card("Найдено email-алиасов", str(len(mailcat_items)), "Mailcat") +
        _metric_card("Сайтов из Holehe", str(len(holehe_items)), f"Проверено: {data['holehe'].get('checked', 0)}") +
        _metric_card("Сайтов из Blackbird", str(len(blackbird_items)), f"Проверено: {data['blackbird'].get('checked', 0)}") +
        _metric_card("Итого совпадений", str(total_hits), "уникальные публичные следы")
    )

    mailcat_html = ''.join(_build_email_row(x) for x in mailcat_items) if mailcat_items else '<div class="empty-block">Совпадений Mailcat не найдено</div>'
    holehe_html = ''.join(_build_site_row(x) for x in holehe_items) if holehe_items else '<div class="empty-block">Holehe ничего не подтвердил</div>'
    blackbird_html = ''.join(_build_site_row(x) for x in blackbird_items) if blackbird_items else '<div class="empty-block">Blackbird ничего не подтвердил</div>'

    errors_html = _build_notice_list(data["holehe"].get("errors", []), "Ошибок Holehe не обнаружено")

    template = _load_template()
    html_report = template.format(
        css_url=html.escape(css_url),
        target_email=html.escape(target_email),
        username=html.escape(username),
        metrics_html=metrics_html,
        mailcat_count=len(mailcat_items),
        mailcat_html=mailcat_html,
        holehe_count=len(holehe_items),
        holehe_checked=data["holehe"].get("checked", 0),
        holehe_html=holehe_html,
        blackbird_count=len(blackbird_items),
        blackbird_checked=data["blackbird"].get("checked", 0),
        blackbird_duration=html.escape(data["blackbird"].get("duration", "") or "—"),
        blackbird_html=blackbird_html,
        errors_html=errors_html,
        holehe_code=data["holehe"].get("return_code", 0),
        mailcat_code=data["mailcat"].get("return_code", 0),
        blackbird_code=data["blackbird"].get("return_code", 0),
    )

    if output_path is None:
        fd, output_path = tempfile.mkstemp(prefix="email_insight_", suffix=".html")
        os.close(fd)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_report)

    return output_path
