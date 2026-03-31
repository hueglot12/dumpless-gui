import requests
import os
import time
from datetime import datetime
import csv
from unidecode import unidecode
import re
from collections import Counter
import json
from dotenv import load_dotenv

load_dotenv()


VK_API = "https://api.vk.com/method"
VERSION = "5.199"

_LAST_CALL = 0

def get_vk_api_token():
    load_dotenv(override=True)
    return os.getenv("VK_API", "").strip()

def normalize_lastname(name: str) -> str:
    if not name:
        return ""

    name = name.strip().lower()
    name = unidecode(name)
    name = re.sub(r"[^a-z]", "", name)

    for suf in ("ova", "eva", "ina"):
        if name.endswith(suf):
            return name[:-1]

    return name


def vk_call(method, params=None):
    global _LAST_CALL

    if params is None:
        params = {}

    token = get_vk_api_token()
    if not token:
        raise Exception("Сначала укажите VK API в настройках")

    delta = time.time() - _LAST_CALL
    if delta < 0.36:
        time.sleep(0.36 - delta)
    _LAST_CALL = time.time()

    params.update({
        "access_token": token,
        "v": VERSION
    })

    r = requests.get(f"{VK_API}/{method}", params=params, timeout=30).json()

    if "error" in r:
        raise Exception(str(r["error"]))

    return r["response"]


def get_all_friends(user_id):
    friends = []
    count = 1000
    offset = 0

    while True:
        resp = vk_call("friends.get", {
            "user_id": user_id,
            "fields": "domain,sex,maiden_name,city,photo_100,first_name,last_name",
            "count": count,
            "offset": offset
        })

        items = resp.get("items", [])
        if not items:
            break

        friends.extend(items)

        if len(items) < count:
            break

        offset += count

    return friends


def save_friends_csv(friends, user_id):
    os.makedirs("friends_lists", exist_ok=True)

    csv_path = f"friends_lists/friends_{user_id}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Имя", "Фамилия", "ID", "Ссылка"])

        for fr in friends:
            writer.writerow([
                fr.get("first_name", ""),
                fr.get("last_name", ""),
                fr.get("id", ""),
                f"https://vk.com/{fr.get('domain', fr.get('id', ''))}"
            ])

    return csv_path


def cleanup_files(*paths):
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def save_same_lastname_csv(friends, owner_id, last_name):
    os.makedirs("same_lastname", exist_ok=True)

    safe_last_name = re.sub(r"[^\w\-а-яА-ЯёЁ]+", "_", last_name)
    filename = f"same_lastname/{safe_last_name}_{owner_id}.csv"

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Имя", "Фамилия", "ID", "Ссылка"])

        for friend in friends:
            first = friend.get("first_name", "")
            last = friend.get("last_name", "")
            fid = friend.get("id", "")
            link = f"https://vk.com/id{fid}"
            writer.writerow([first, last, fid, link])

    return filename


def filter_same_lastname(friends: list, target_last_name: str, sex: int | None = None, city: str | None = None):
    result = []

    base_target = normalize_lastname(target_last_name)
    if not base_target:
        return result

    for f in friends:
        candidates = [f.get("last_name", "")]
        maiden = f.get("maiden_name")
        if maiden:
            candidates.append(maiden)

        matched = False
        for name in candidates:
            if normalize_lastname(name) == base_target:
                matched = True
                break

        if not matched:
            continue

        if sex is not None and f.get("sex") != sex:
            continue

        if city:
            city_title = f.get("city", {}).get("title", "")
            if not city_title or city.casefold() not in city_title.casefold():
                continue

        result.append(f)

    return result


def find_same_lastname_people(user_id, last_name, sex=None, city=None):
    friends = get_all_friends(user_id)

    same_lastname = filter_same_lastname(
        friends=friends,
        target_last_name=last_name,
        sex=sex,
        city=city
    )

    csv_path = save_same_lastname_csv(same_lastname, user_id, last_name)

    return same_lastname, csv_path


def download_avatar(url, user_id):
    if not url:
        return None

    os.makedirs("avatars", exist_ok=True)
    path = f"avatars/{user_id}.jpg"

    img = requests.get(url, timeout=30).content
    with open(path, "wb") as f:
        f.write(img)

    return path


def format_last_seen(ts):
    if not ts:
        return "Скрыто"
    return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")


def calculate_profile_metrics(user, same_lastname):
    followers = user.get("followers_count", 0)

    open_fields = sum([
        bool(user.get("city")),
        bool(user.get("bdate")),
        bool(user.get("status")),
        bool(user.get("followers_count"))
    ])
    privacy_score = int((open_fields / 4) * 100)

    male_same = sum(1 for f in same_lastname if f.get("sex") == 2)
    female_same = sum(1 for f in same_lastname if f.get("sex") == 1)

    cities = [f.get("city", {}).get("title") for f in same_lastname if f.get("city")]
    city_clusters = Counter(cities)

    return {
        "followers": followers,
        "privacy_score": privacy_score,
        "male_same": male_same,
        "female_same": female_same,
        "city_clusters": city_clusters,
        "report_time": datetime.now().strftime("%d.%m.%Y %H:%M")
    }


def vk_profile_info(num, friends_count=10):
    num = str(num)
    num = num.replace("https://vk.com/", "").replace("http://vk.com/", "").replace("@", "").strip()

    user = vk_call("users.get", {
        "user_ids": num,
        "fields": "city,bdate,followers_count,last_seen,photo_max_orig,status"
    })[0]

    user_vk_id = user["id"]
    avatar_path = download_avatar(user.get("photo_max_orig"), user_vk_id)
    last_name = user["last_name"]

    friends_list = []
    try:
        friends_list = vk_call("friends.get", {
            "user_id": user_vk_id,
            "fields": "first_name,last_name,domain",
            "count": friends_count
        }).get("items", [])
    except Exception as e:
        print("friends preview error:", e)

    return user, avatar_path, friends_list, last_name, user_vk_id


def generate_html_report(user, friends_preview, same_lastname, avatar_path, metrics, output_file="vk_insight_report.html"):
    import json

    friends_html = "".join(
        f"<li>{f['first_name']} {f['last_name']} — vk.com/{f.get('domain','id'+str(f['id']))}</li>"
        for f in friends_preview
    ) or "<li>Список скрыт</li>"

    colors = ["#4e73df","#1cc88a","#36b9cc","#f6c23e","#e74a3b","#858796"]
    clusters_html = ""
    for i, (city, count) in enumerate(metrics["city_clusters"].items()):
        color = colors[i % len(colors)]
        clusters_html += f"<div class='cluster' style='background:{color}'>{city}: {count}</div>"
    if not clusters_html:
        clusters_html = "<div class='cluster'>Нет данных</div>"

    same_lastname_json = json.dumps([
        {
            "id": f["id"],
            "name": f"{f.get('first_name','')} {f.get('last_name','')}",
            "sex": f.get("sex"),
            "city": f.get("city", {}).get("title", "Не указан"),
            "photo": f.get("photo_100") or "https://vk.com/images/camera_200.png",
            "domain": f.get("domain", f"id{f['id']}")
        }
        for f in same_lastname
    ], ensure_ascii=False)

    avatar_src = f"/files/{avatar_path}" if avatar_path else "https://vk.com/images/camera_200.png"

    html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>VK Insight Report</title>
<style>
body {{ font-family: Arial, sans-serif; background:#f4f6f9; margin:0; padding:20px; color:#2c3e50; }}
.header {{ background:linear-gradient(135deg,#4e73df,#1cc88a); color:white; padding:25px; border-radius:12px; }}
.section {{ background:white; margin-top:20px; padding:20px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.05); }}
h2 {{ margin-top:0; border-left:5px solid #4e73df; padding-left:10px; }}
.metrics {{ display:flex; gap:20px; flex-wrap:wrap; }}
.metric {{ background:#eef2ff; padding:15px; border-radius:10px; flex:1; min-width:180px; text-align:center; }}
.metric h3 {{ margin:0; font-size:22px; color:#4e73df; }}
.friend-list li {{ margin-bottom:6px; }}
.cluster {{
    display:inline-block;
    padding:8px 14px;
    margin:6px;
    border-radius:20px;
    color:white;
    font-weight:bold;
    font-size:13px;
}}
.footer {{ text-align:center; margin-top:30px; font-size:12px; color:#7f8c8d; }}
.avatar {{ width:120px; border-radius:50%; margin-top:10px; }}
.node-img {{
    width:64px;
    height:64px;
    border-radius:50%;
    object-fit:cover;
    border:3px solid white;
    box-shadow:0 4px 10px rgba(0,0,0,0.15);
    cursor:pointer;
    transition:transform .2s ease;
}}
.node-img:hover {{
    transform:scale(1.08);
}}
.node-label {{
    text-align:center;
    font-size:12px;
    margin-top:6px;
    width:90px;
}}
.graph-container {{
    position:relative;
    width:100%;
    height:480px;
}}
.center-node {{
    position:absolute;
    left:50%;
    top:50%;
    transform:translate(-50%, -50%);
    text-align:center;
}}
.relative-node {{
    position:absolute;
    text-align:center;
    width:90px;
}}
svg {{
    position:absolute;
    width:100%;
    height:100%;
    pointer-events:none;
}}
line {{
    stroke:#d1d3e2;
    stroke-width:2;
}}
</style>
</head>
<body>

<div class="header">
    <h1>VK INSIGHT REPORT</h1>
    <h3>{user['first_name']} {user['last_name']}</h3>
    <img src="{avatar_src}" class="avatar">
</div>

<div class="section">
    <h2>📌 Основная информация</h2>
    <p><b>VK ID:</b> {user['id']}</p>
    <p><b>Город:</b> {user.get('city', {}).get('title', 'Не указан')}</p>
    <p><b>Дата рождения:</b> {user.get('bdate', 'Не указана')}</p>
    <p><b>Статус:</b> {user.get('status', 'Нет статуса')}</p>
</div>

<div class="section">
    <h2>📊 Профильные метрики</h2>
    <div class="metrics">
        <div class="metric"><h3>{metrics['followers']}</h3>Подписчики</div>
        <div class="metric"><h3>{metrics['privacy_score']}%</h3>Заполненность профиля</div>
        <div class="metric"><h3>{len(same_lastname)}</h3>Однофамильцы</div>
        <div class="metric"><h3>{metrics['male_same']}♂ / {metrics['female_same']}♀</h3>Гендер однофамильцев</div>
    </div>
</div>

<div class="section">
    <h2>👥 Друзья (превью)</h2>
    <ul class="friend-list">{friends_html}</ul>
</div>

<div class="section">
    <h2>🌍 Кластеры однофамильцев по городам</h2>
    {clusters_html}
</div>

<div class="section">
    <h2>🕸 Связь с однофамильцами</h2>
    <div class="graph-container">
        <svg id="lines"></svg>
        <div class="center-node">
            <img src="{avatar_src}" class="node-img">
            <div class="node-label"><b>{user['first_name']}<br>{user['last_name']}</b></div>
        </div>
    </div>
</div>

<div class="footer">
    Отчёт сформирован: {metrics['report_time']}<br>
    VK Insight System
</div>

<script>
const data = {same_lastname_json};
const container = document.querySelector(".graph-container");
const svg = document.getElementById("lines");

const centerX = container.clientWidth / 2;
const centerY = container.clientHeight / 2;
const radius = 180;

function drawLine(x1,y1,x2,y2){{
    const line=document.createElementNS("http://www.w3.org/2000/svg","line");
    line.setAttribute("x1",x1);
    line.setAttribute("y1",y1);
    line.setAttribute("x2",x2);
    line.setAttribute("y2",y2);
    svg.appendChild(line);
}}

data.forEach((p,i)=>{{
    const angle = data.length ? (i / data.length) * 2 * Math.PI : 0;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);

    const node = document.createElement("div");
    node.className = "relative-node";
    node.style.left = (x - 45) + "px";
    node.style.top = (y - 45) + "px";

    node.innerHTML = `
        <a href="https://vk.com/${{p.domain}}" target="_blank">
            <img src="${{p.photo}}" class="node-img">
        </a>
        <div class="node-label">${{p.name}}</div>
    `;

    container.appendChild(node);
    drawLine(centerX, centerY, x, y);
}});
</script>

</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    return output_file


def build_vk_insight_html(user_link):
    user, avatar_path, friends_list, last_name, user_vk_id = vk_profile_info(user_link)

    same_lastname, _ = find_same_lastname_people(user_vk_id, last_name)

    full_user = vk_call("users.get", {
        "user_ids": user_vk_id,
        "fields": "city,bdate,followers_count,status"
    })[0]

    metrics = calculate_profile_metrics(full_user, same_lastname)

    report_path = generate_html_report(
        user=full_user,
        friends_preview=friends_list,
        same_lastname=same_lastname,
        avatar_path=avatar_path,
        metrics=metrics
    )

    return report_path