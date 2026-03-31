import re
import smtplib
import socket
from dataclasses import dataclass, asdict

import dns.resolver


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class EmailCheckResult:
    email: str
    status: str          # valid / invalid / unknown
    stage: str           # syntax / dns / smtp
    mx_host: str | None
    smtp_code: int | None
    smtp_message: str
    detail: str


def get_mx_hosts(domain: str) -> list[str]:
    answers = dns.resolver.resolve(domain, "MX")
    records = sorted(answers, key=lambda r: r.preference)
    return [str(r.exchange).rstrip(".") for r in records]


def check_email_smtp(
    email: str,
    helo_host: str = "example.com",
    mail_from: str = "probe@example.com",
    timeout: int = 10,
) -> EmailCheckResult:
    email = email.strip()

    if not EMAIL_RE.match(email):
        return EmailCheckResult(
            email=email,
            status="invalid",
            stage="syntax",
            mx_host=None,
            smtp_code=None,
            smtp_message="",
            detail="Некорректный формат email",
        )

    domain = email.split("@", 1)[1]

    try:
        mx_hosts = get_mx_hosts(domain)
    except Exception as e:
        return EmailCheckResult(
            email=email,
            status="unknown",
            stage="dns",
            mx_host=None,
            smtp_code=None,
            smtp_message="",
            detail=f"Не удалось получить MX-записи: {e}",
        )

    if not mx_hosts:
        return EmailCheckResult(
            email=email,
            status="unknown",
            stage="dns",
            mx_host=None,
            smtp_code=None,
            smtp_message="",
            detail="У домена нет MX-записей",
        )

    last_error = None

    for mx_host in mx_hosts:
        server = None
        try:
            server = smtplib.SMTP(timeout=timeout)
            server.connect(mx_host, 25)
            server.ehlo(helo_host)

            # Некоторые серверы требуют MAIL FROM перед RCPT TO
            server.mail(mail_from)
            code, msg = server.rcpt(email)

            if isinstance(msg, bytes):
                msg = msg.decode(errors="replace")
            else:
                msg = str(msg)

            try:
                server.quit()
            except Exception:
                pass

            if code in (250, 251):
                return EmailCheckResult(
                    email=email,
                    status="valid",
                    stage="smtp",
                    mx_host=mx_host,
                    smtp_code=code,
                    smtp_message=msg,
                    detail="Сервер принял RCPT TO, адрес вероятно существует",
                )

            if code in (550, 551, 553):
                return EmailCheckResult(
                    email=email,
                    status="invalid",
                    stage="smtp",
                    mx_host=mx_host,
                    smtp_code=code,
                    smtp_message=msg,
                    detail="Сервер явно отверг адрес",
                )

            return EmailCheckResult(
                email=email,
                status="unknown",
                stage="smtp",
                mx_host=mx_host,
                smtp_code=code,
                smtp_message=msg,
                detail="Сервер ответил неоднозначно",
            )

        except (socket.timeout, socket.gaierror, smtplib.SMTPException, OSError) as e:
            last_error = f"{mx_host}: {e}"ы
        finally:
            if server is not None:
                try:
                    server.close()
                except Exception:
                    pass

    return EmailCheckResult(
        email=email,
        status="unknown",
        stage="smtp",
        mx_host=None,
        smtp_code=None,
        smtp_message="",
        detail=f"Не удалось проверить ни через один MX-сервер. Последняя ошибка: {last_error}",
    )


