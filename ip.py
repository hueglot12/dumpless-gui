import os
import requests


def ip_info(ip_address: str) -> dict:
    response = requests.get(f"http://ip-api.com/json/{ip_address}?lang=ru", timeout=10)

    if response.status_code != 200:
        raise Exception("Ошибка при получении информации об IP")

    info = response.json()
    if info.get("status") == "fail":
        raise Exception(info.get("message", "Не удалось получить данные"))

    lat = info.get("lat")
    lon = info.get("lon")

    return {
        "ip": info.get("query", ip_address),
        "country": info.get("country", "Неизвестно"),
        "country_code": info.get("countryCode", "Неизвестно"),
        "region": info.get("regionName", info.get("region", "Неизвестно")),
        "city": info.get("city", "Неизвестно"),
        "zip": info.get("zip", "Неизвестно"),
        "timezone": info.get("timezone", "Неизвестно"),
        "isp": info.get("isp", "Неизвестно"),
        "org": info.get("org", "Неизвестно"),
        "as_name": info.get("as", "Неизвестно"),
        "lat": lat,
        "lon": lon,
        "maps_label": f"{info.get('city', 'Неизвестно')}, {info.get('regionName', info.get('region', 'Неизвестно'))}, {info.get('country', 'Неизвестно')}",
    }


def build_overpass_query(lat: float, lon: float, radius: int = 1200) -> str:
    return f"""
    [out:json][timeout:20];
    (
      node(around:{radius},{lat},{lon})[amenity];
      node(around:{radius},{lat},{lon})[shop];
      node(around:{radius},{lon})[office];
      way(around:{radius},{lat},{lon})[amenity];
      way(around:{radius},{lat},{lon})[shop];
      way(around:{radius},{lat},{lon})[office];
    );
    out center 40;
    """.strip()


def fetch_nearby_places(lat: float | None, lon: float | None) -> list[dict]:
    if lat is None or lon is None:
        return []

    query = f"""
    [out:json][timeout:20];
    (
      node(around:1200,{lat},{lon})[amenity];
      node(around:1200,{lat},{lon})[shop];
      node(around:1200,{lat},{lon})[office];
      way(around:1200,{lat},{lon})[amenity];
      way(around:1200,{lat},{lon})[shop];
      way(around:1200,{lat},{lon})[office];
    );
    out center 40;
    """.strip()

    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data=query.encode("utf-8"),
            headers={"Content-Type": "text/plain; charset=utf-8"},
            timeout=25,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    places = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue

        amenity = tags.get("amenity")
        shop = tags.get("shop")
        office = tags.get("office")
        kind = amenity or shop or office or "место"

        place_lat = el.get("lat")
        place_lon = el.get("lon")

        if place_lat is None or place_lon is None:
            center = el.get("center", {})
            place_lat = center.get("lat")
            place_lon = center.get("lon")

        places.append({
            "name": name,
            "kind": kind,
            "lat": place_lat,
            "lon": place_lon,
        })

    return places[:20]


def generate_ip_html_report_sync(data: dict, output_file: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "htmls", "ip.html")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    nearby_places = fetch_nearby_places(data["lat"], data["lon"])

    places_html = "".join(
        f"<li><b>{p['name']}</b> <span class='place-type'>{p['kind']}</span></li>"
        for p in nearby_places
    ) or "<li>Поблизости ничего не найдено</li>"

    markers_js = ""
    for p in nearby_places:
        if p["lat"] is None or p["lon"] is None:
            continue
        safe_name = p["name"].replace("'", "\\'")
        safe_kind = p["kind"].replace("'", "\\'")
        markers_js += (
            f"L.marker([{p['lat']}, {p['lon']}]).addTo(map)"
            f".bindPopup('<b>{safe_name}</b><br>{safe_kind}');\n"
        )

    html = template.format(
        ip=data["ip"],
        country=data["country"],
        country_code=data["country_code"],
        region=data["region"],
        city=data["city"],
        zip_code=data["zip"],
        timezone=data["timezone"],
        isp=data["isp"],
        org=data["org"],
        as_name=data["as_name"],
        lat=data["lat"] if data["lat"] is not None else "null",
        lon=data["lon"] if data["lon"] is not None else "null",
        maps_label=data["maps_label"],
        places_html=places_html,
        markers_js=markers_js,
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    return output_file


def build_ip_insight_html(ip_address: str) -> str:
    data = ip_info(ip_address)

    output_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ip_insight_report.html"
    )

    generate_ip_html_report_sync(data, output_file)
    return output_file