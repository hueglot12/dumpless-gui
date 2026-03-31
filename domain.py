import whois as whois_module
import subprocess
import socket
import ssl
from datetime import datetime, timezone
import os
import asyncio

MAX_SUBDOMAINS = 600

SUSPICIOUS_KEYWORDS = [
    "admin", "panel", "cp", "dashboard",
    "pay", "payment", "billing",
    "auth", "login", "secure", "account"
]


def normalize_domain(domain: str) -> str:
    domain = domain.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "").replace("www.", "")
    domain = domain.split("/")[0].split(":")[0]
    return domain


def has_https_sync(domain: str) -> bool:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain):
                return True
    except Exception:
        return False


def calculate_risk(age_days, https, suspicious_count, total_subs):
    score = 0

    if age_days is not None:
        if age_days < 30:
            score += 25
        elif age_days < 180:
            score += 10

    if not https:
        score += 20

    score += min(suspicious_count * 2, 10)

    if total_subs <= 1:
        score += 5

    return min(score, 100)


def get_domain_age_days(whois_obj) -> int | None:
    cd = getattr(whois_obj, "creation_date", None)

    if isinstance(cd, list):
        cd = cd[0]

    if not cd:
        return None

    if not isinstance(cd, datetime):
        return None

    now = datetime.now(timezone.utc)

    if cd.tzinfo is None:
        cd = cd.replace(tzinfo=timezone.utc)

    return (now - cd).days


def get_subdomains_subfinder_sync(domain: str, limit: int = MAX_SUBDOMAINS) -> list[str]:
    try:
        process = subprocess.Popen(
            ["subfinder", "-silent", "-d", domain],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        subdomains = []
        for line in process.stdout:
            if len(subdomains) >= limit:
                process.kill()
                break
            item = line.strip()
            if item:
                subdomains.append(item)

        return subdomains
    except Exception:
        return []


def analyze_subdomains(subdomains: list[str]) -> list[str]:
    result = []
    for s in subdomains:
        for k in SUSPICIOUS_KEYWORDS:
            if k in s.lower():
                result.append(s)
                break
    return result

def generate_domain_html_report_sync(data: dict, output_file: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "htmls", "domain.html")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    subs_html = "".join(f"<li>{s}</li>" for s in data["subdomains"]) or "<li>Не найдены</li>"
    suspicious_html = "".join(
        f"<span class='cluster' style='background:#e74a3b'>{s}</span>"
        for s in data["suspicious_subdomains"]
    ) or "<span class='cluster' style='background:#858796'>Нет</span>"

    risk_color = (
        "#1cc88a" if data["risk_score"] < 30 else
        "#f6c23e" if data["risk_score"] < 60 else
        "#e74a3b"
    )

    html = template.format(
        domain=data["domain"],
        registrar=data["registrar"],
        age_days=data["age_days"],
        https_label="✅ Есть" if data["https"] else "❌ Нет",
        subdomains_count=len(data["subdomains"]),
        suspicious_html=suspicious_html,
        subs_html=subs_html,
        risk_color=risk_color,
        risk_score=data["risk_score"],
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    return output_file


def whois_full_sync(domain_name: str) -> dict:
    domain_name = normalize_domain(domain_name)

    try:
        w = whois_module.whois(domain_name)
    except Exception as e:
        return {"error": str(e)}

    subdomains = get_subdomains_subfinder_sync(domain_name)
    suspicious = analyze_subdomains(subdomains)
    https = has_https_sync(domain_name)
    age_days = get_domain_age_days(w)

    risk = calculate_risk(
        age_days,
        https,
        len(suspicious),
        len(subdomains)
    )

    return {
        "domain": domain_name,
        "registrar": getattr(w, "registrar", "Нет данных"),
        "creation_date": getattr(w, "creation_date", None),
        "expiration_date": getattr(w, "expiration_date", None),
        "emails": getattr(w, "emails", []),
        "name_servers": getattr(w, "name_servers", []),
        "age_days": age_days if age_days is not None else 0,
        "https": https,
        "subdomains": subdomains,
        "suspicious_subdomains": suspicious,
        "risk_score": risk
    }


def build_domain_insight_html(domain: str) -> str:
    data = whois_full_sync(domain)

    if "error" in data:
        raise Exception(data["error"])

    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "domain_insight_report.html"
    )

    generate_domain_html_report_sync(data, output_file)
    return output_file


async def whois_full(domain: str) -> dict:
    return await asyncio.to_thread(whois_full_sync, domain)


async def generate_domain_html_report(data: dict, output_file: str):
    return await asyncio.to_thread(
        generate_domain_html_report_sync,
        data,
        output_file
    )