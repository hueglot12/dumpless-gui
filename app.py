from flask import Flask, request, jsonify, send_file, send_from_directory
import os
import vk_logic
import asyncio
import domain
from PhoneOsint import phone_search
import ip
from dotenv import load_dotenv
import binosint
from email_osint import run_email_osint, build_email_report_html
from smtp_check import check_email_smtp
import traceback

app = Flask(__name__)

LAST_REPORT_PATH = "vk_insight_report.html"
LAST_DOMAIN_REPORT_PATH = "domain_insight_report.html"
LAST_IP_REPORT_PATH = "ip_insight_report.html"
LAST_EMAIL_REPORT_PATH = "email_insight_report.html"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")


def read_vk_api() -> str:
    load_dotenv(override=True)
    return os.getenv("VK_API", "").strip()


def write_vk_api(token: str):
    lines = []

    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

    found = False
    new_lines = []

    for line in lines:
        if line.startswith("VK_API="):
            new_lines.append(f"VK_API={token}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"VK_API={token}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    os.environ["VK_API"] = token

@app.route("/settings/vk_api", methods=["GET"])
def get_vk_api():
    token = read_vk_api()
    return jsonify({
        "ok": True,
        "token": token
    })


@app.route("/settings/vk_api", methods=["POST"])
def set_vk_api():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()

    try:
        write_vk_api(token)
        return jsonify({
            "ok": True
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route("/", methods=["GET"])
def index():
    return "VK Insight backend is running"

@app.route("/bin_search", methods=["POST"])
def bin_search_route():
    data = request.get_json(silent=True) or {}
    card_or_bin = data.get("bin", "").strip()

    if not card_or_bin:
        return jsonify({"ok": False, "error": "BIN или номер карты не передан"}), 400

    try:
        result = binosint.bin_info(card_or_bin)
        return jsonify({
            "ok": True,
            "result": result
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route("/domain.css", methods=["GET"])
def domain_css():
    css_path = os.path.join(os.getcwd(), "htmls", "domain.css")
    print("[CSS] path:", css_path)
    print("[CSS] exists:", os.path.exists(css_path))
    return send_file(css_path, mimetype="text/css")

@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    safe_path = os.path.abspath(filename)
    base_path = os.path.abspath(os.getcwd())

    if not safe_path.startswith(base_path):
        return "Access denied", 403

    directory = os.path.dirname(safe_path)
    name = os.path.basename(safe_path)
    return send_from_directory(directory, name)

@app.route("/ip_analyze", methods=["POST"])
def ip_analyze():
    global LAST_IP_REPORT_PATH

    data = request.get_json(silent=True) or {}
    ip_address = data.get("ip", "").strip()

    if not ip_address:
        return jsonify({"ok": False, "error": "IP не передан"}), 400

    try:
        print(f"[IP] start: {ip_address}")

        report_path = ip.build_ip_insight_html(ip_address)
        LAST_IP_REPORT_PATH = report_path

        print(f"[IP] done: {report_path}")

        return jsonify({
            "ok": True,
            "report_url": "http://127.0.0.1:5000/report/ip/latest"
        })
    except Exception as e:
        print(f"[IP] error: {e}")
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/report/ip/latest", methods=["GET"])
def latest_ip_report():
    if not os.path.exists(LAST_IP_REPORT_PATH):
        return "IP report not found", 404
    return send_file(LAST_IP_REPORT_PATH)


@app.route("/report/latest", methods=["GET"])
def latest_report():
    if not os.path.exists(LAST_REPORT_PATH):
        return "Report not found", 404
    return send_file(LAST_REPORT_PATH)


@app.route("/report/domain/latest", methods=["GET"])
def latest_domain_report():
    if not os.path.exists(LAST_DOMAIN_REPORT_PATH):
        return "Domain report not found", 404
    return send_file(LAST_DOMAIN_REPORT_PATH)


@app.route("/analyze", methods=["POST"])
def analyze():
    global LAST_REPORT_PATH

    data = request.get_json(silent=True) or {}
    link = data.get("link", "").strip()

    if not link:
        return jsonify({"ok": False, "error": "Ссылка не передана"}), 400

    vk_api = read_vk_api()
    if not vk_api:
        return jsonify({
            "ok": False,
            "error": "Сначала укажите VK API в настройках"
        }), 400

    try:
        print(f"[ANALYZE] start: {link}")

        report_path = vk_logic.build_vk_insight_html(link)
        LAST_REPORT_PATH = report_path

        print(f"[ANALYZE] done: {report_path}")

        return jsonify({
            "ok": True,
            "report_url": "http://127.0.0.1:5000/report/latest"
        })
    except Exception as e:
        print(f"[ANALYZE] error: {e}")
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route("/phone_search", methods=["POST"])
def phone_search_route():
    data = request.get_json(silent=True) or {}
    phone = data.get("phone", "").strip()

    if not phone:
        return jsonify({"ok": False, "error": "Номер не передан"}), 400

    try:
        result = asyncio.run(phone_search(phone))
        return jsonify({
            "ok": True,
            "result": result
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500



@app.route("/email_report.css", methods=["GET"])
def email_report_css():
    css_path = os.path.join(os.getcwd(), "htmls", "email_report.css")
    return send_file(css_path, mimetype="text/css")

@app.route("/report/email/latest", methods=["GET"])
def latest_email_report():
    if not os.path.exists(LAST_EMAIL_REPORT_PATH):
        return "Email report not found", 404
    return send_file(LAST_EMAIL_REPORT_PATH)

@app.route("/email_analyze", methods=["POST"])
def email_analyze():
    global LAST_EMAIL_REPORT_PATH

    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()

    if not email:
        return jsonify({"ok": False, "error": "Email не передан"}), 400

    try:
        print(f"[EMAIL] start: {email}")
        result = asyncio.run(run_email_osint(email))
        report_path = build_email_report_html(result, output_path="email_osint_report.html")
        LAST_EMAIL_REPORT_PATH = report_path
        print(f"[EMAIL] done: {report_path}")

        return jsonify({
            "ok": True,
            "report_url": "http://127.0.0.1:5000/report/email/latest"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route("/domain_analyze", methods=["POST"])
def domain_analyze():
    global LAST_DOMAIN_REPORT_PATH

    data = request.get_json(silent=True) or {}
    domain_name = data.get("domain", "").strip()

    if not domain_name:
        return jsonify({"ok": False, "error": "Домен не передан"}), 400

    try:
        print(f"[DOMAIN] start: {domain_name}")

        report_path = domain.build_domain_insight_html(domain_name)
        LAST_DOMAIN_REPORT_PATH = report_path

        print(f"[DOMAIN] done: {report_path}")

        return jsonify({
            "ok": True,
            "report_url": "http://127.0.0.1:5000/report/domain/latest"
        })
    except Exception as e:
        print(f"[DOMAIN] error: {e}")
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)