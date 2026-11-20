import streamlit as st
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
import pandas as pd

DB = Path(__file__).with_name("highway_alerts.db")
API = "https://api.open-meteo.com/v1/forecast"

# Representative monitoring points for the expo prototype.
# These are town-level weather points, NOT exact road-segment sensors.
POINTS = {
    "Quetta–Zhob": [
        ("Quetta", 30.1798, 66.9750),
        ("Qilla Saifullah", 30.7000, 68.3600),
        ("Zhob", 31.3411, 69.4481),
    ],
    "Quetta–Karachi": [
        ("Quetta", 30.1798, 66.9750),
        ("Khuzdar", 27.8000, 66.6167),
    ],
    "Quetta–Sibi": [
        ("Quetta", 30.1798, 66.9750),
        ("Sibi", 29.5430, 67.8773),
    ],
    "Quetta–Chaman": [
        ("Quetta", 30.1798, 66.9750),
        ("Chaman", 30.9177, 66.4526),
    ],
    "Quetta–Nushki–Dalbandin": [
        ("Quetta", 30.1798, 66.9750),
        ("Nushki", 29.5522, 66.0215),
        ("Dalbandin", 28.8885, 64.4062),
    ],
    "Quetta–Loralai": [
        ("Quetta", 30.1798, 66.9750),
        ("Loralai", 30.3705, 68.5979),
    ],
}
ROUTES = list(POINTS.keys())
LANGUAGES = ["Urdu", "Pashto", "Balochi"]
ROAD_STATUSES = ["Open (operator entered)", "Restricted", "Closed", "Clearance Pending"]

st.set_page_config(page_title="Balochistan Highway Watch", page_icon="🛣️", layout="wide", initial_sidebar_state="expanded")

def logo_svg():
    return """<svg xmlns="http://www.w3.org/2000/svg" width="84" height="84" viewBox="0 0 100 100">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#14b8a6"/><stop offset="1" stop-color="#2563eb"/></linearGradient></defs>
    <rect x="3" y="3" width="94" height="94" rx="27" fill="#0b1728" stroke="#24415c" stroke-width="2"/>
    <path d="M18 70 Q32 51 48 58 T82 31" fill="none" stroke="url(#g)" stroke-width="8" stroke-linecap="round"/>
    <path d="M21 78 L35 51 L45 60 L59 34 L77 51" fill="none" stroke="#e2e8f0" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M49 15 C39 15 32 23 32 33 C32 46 49 57 49 57 C49 57 66 46 66 33 C66 23 59 15 49 15Z" fill="#14b8a6"/>
    <circle cx="49" cy="32" r="6" fill="#082f49"/>
    <path d="M16 84 H84" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>
    </svg>"""

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL,
            vehicle TEXT NOT NULL, route TEXT NOT NULL, language TEXT NOT NULL, created_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS checkpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, route TEXT NOT NULL, location TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS road_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT, route TEXT NOT NULL, area TEXT NOT NULL,
            status TEXT NOT NULL, authority_note TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, driver_id INTEGER, route TEXT NOT NULL,
            message TEXT NOT NULL, channel TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL)""")

def rows(q, p=()):
    with connect() as con:
        return [dict(x) for x in con.execute(q, p).fetchall()]

def run(q, p=()):
    with connect() as con:
        cur = con.execute(q, p)
        con.commit()
        return cur.lastrowid

def seed():
    if not rows("SELECT id FROM checkpoints LIMIT 1"):
        for route, pts in POINTS.items():
            for name, _, _ in pts:
                run("INSERT INTO checkpoints(name,route,location) VALUES(?,?,?)",
                    (f"{name} Weather Checkpoint (virtual)", route, name))
    if not rows("SELECT id FROM road_status LIMIT 1"):
        for route, pts in POINTS.items():
            for name, _, _ in pts:
                run("INSERT INTO road_status(route,area,status,authority_note,updated_at) VALUES(?,?,?,?,?)",
                    (route, name, "Clearance Pending", "Not connected to road authority; verify locally", datetime.now().isoformat(timespec="minutes")))

@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather(lat, lon):
    params = {
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,wind_gusts_10m,visibility",
        "hourly": "temperature_2m,precipitation_probability,precipitation,visibility,wind_speed_10m,weather_code",
        "forecast_days": 2, "timezone": "Asia/Karachi"
    }
    response = requests.get(API, params=params, timeout=15)
    response.raise_for_status()
    return response.json()

def weather_label(code):
    if code == 0: return "صاف"
    if code in (1,2,3): return "جزوی / مکمل ابر آلود"
    if code in (45,48): return "دھند"
    if code in (51,53,55,56,57): return "ہلکی بوندا باندی"
    if code in (61,63,65,66,67,80,81,82): return "بارش"
    if code in (71,73,75,77,85,86): return "برف باری"
    if code in (95,96,99): return "گرج چمک"
    return f"Weather code {code}"

def alert_text(area, weather_text, road):
    if road == "Closed":
        return f"سرکاری سڑک اطلاع: {area} کے مقام پر سڑک بند ہونے کی اطلاع درج ہے۔ براہِ کرم آگے سفر نہ کریں۔ متعلقہ ادارے کی جانب سے سڑک کھلنے کی تصدیق کا انتظار کریں۔"
    if road in ("Restricted", "Clearance Pending"):
        return f"احتیاط: {area} کے مقام پر سڑک کی حیثیت: {road}۔ سفر سے پہلے متعلقہ حکام سے تازہ تصدیق کریں۔"
    return f"موسمی اطلاع: {area} کے مقام پر {weather_text} کی صورتحال ریکارڈ ہوئی ہے۔ رفتار اور محفوظ فاصلے کا خیال رکھیں۔ یہ موسمی اطلاع ہے، سڑک کھلی ہونے کی تصدیق نہیں۔"

init_db()
seed()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap');
:root {--bg:#07111f;--panel:#101e31;--muted:#8fa5bf;--teal:#2dd4bf;--blue:#60a5fa;}
.stApp {background: radial-gradient(ellipse at 15% 0%, #12314a 0%, #07111f 48%, #081321 100%); color:#e8f0fa;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#0b192a,#101f33); border-right:1px solid #1e3853;}
.block-container {padding-top:1.5rem; max-width:1500px;}
h1,h2,h3 {color:#f1f7ff!important; font-family:Inter,sans-serif;}
p, label, .stMarkdown {color:#d4e0ee;}
.hero {background:linear-gradient(115deg,rgba(20,184,166,.19),rgba(37,99,235,.15));border:1px solid #28516b;border-radius:22px;padding:22px 26px;margin-bottom:18px;}
.hero-title {font-size:27px;font-weight:800;color:#f8fbff;letter-spacing:-.5px;}
.hero-sub {color:#9db6cc;font-size:13px;margin-top:5px;}
.metric {background:linear-gradient(145deg,#13263b,#0d1a2b);border:1px solid #24415c;border-radius:16px;padding:16px 18px;}
.metric-label {font-size:12px;color:#9ab0c8;}
.metric-value {font-size:28px;font-weight:800;color:#eaf7ff;}
.pill {display:inline-block;border-radius:999px;padding:4px 10px;background:#123e45;color:#8df2df;font-size:11px;font-weight:700;}
div[data-testid="stForm"],div[data-testid="stDataFrame"],.stAlert {border-radius:14px;}
.stButton>button {border-radius:10px;border:1px solid #2b6472;background:linear-gradient(90deg,#0f766e,#1d4ed8);color:white;font-weight:700;}
.stButton>button:hover {border-color:#5eead4;color:white;}
small {color:#9ab0c8;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f'<div style="display:flex;gap:12px;align-items:center;margin:4px 0 22px">{logo_svg()}<div><div style="font-weight:800;font-size:17px;color:#f0f8ff">HIGHWAY WATCH</div><div style="font-size:10px;color:#8fa5bf;letter-spacing:1.2px">BALOCHISTAN • EARLY WARNING</div></div></div>', unsafe_allow_html=True)
    page = st.radio("MAIN MENU", ["Overview", "Live Weather", "Driver Registry", "Road Status", "Checkpoints", "Alert Centre", "Alert History"], label_visibility="visible")
    st.markdown("---")
    st.markdown('<span class="pill">LIVE WEATHER API</span>', unsafe_allow_html=True)
    st.caption("Open-Meteo forecast feed • 10-minute cache")
    st.caption("Weather feed is not a road closure authority.")

st.markdown(f'<div class="hero"><div style="display:flex;align-items:center;gap:16px">{logo_svg()}<div><div class="hero-title">Balochistan Smart Highway Watch</div><div class="hero-sub">AI-assisted weather awareness • Route monitoring • Urdu driver alerts</div><div style="margin-top:10px"><span class="pill">EXPO PROTOTYPE</span></div></div></div></div>', unsafe_allow_html=True)

if page == "Overview":
    drivers = rows("SELECT * FROM drivers")
    cps = rows("SELECT * FROM checkpoints")
    alerts = rows("SELECT * FROM alerts")
    roads = rows("SELECT * FROM road_status")
    a,b,c,d = st.columns(4)
    for col, label, val in [(a,"Registered drivers",len(drivers)),(b,"Virtual checkpoints",len(cps)),(c,"Road records",len(roads)),(d,"Alerts generated",len(alerts))]:
        col.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value">{val}</div></div>',unsafe_allow_html=True)
    st.markdown("### Monitored Balochistan corridors")
    for route, pts in POINTS.items():
        st.markdown(f"**{route}**  ·  " + "  →  ".join(p[0] for p in pts))

    st.markdown("### Corridor reference map")
    map_rows = []
    for route_name, route_points in POINTS.items():
        for town, latitude, longitude in route_points:
            map_rows.append({"lat": latitude, "lon": longitude, "Location": town, "Route": route_name})
    st.map(pd.DataFrame(map_rows), latitude="lat", longitude="lon", use_container_width=True)
    st.caption("Map pins show representative town-level forecast points, not surveyed road alignments or physical sensors.")
    st.info("Weather is fetched from a live public forecast API when you open Live Weather. Road status remains unverified until an authorized source is integrated.")

elif page == "Live Weather":
    st.subheader("Live forecast by route location")
    st.caption("Open-Meteo live API response. Forecast points are town-level reference coordinates, not sensors placed along every kilometre of road.")
    route = st.selectbox("Choose highway", ROUTES)
    if st.button("Refresh weather now"):
        fetch_weather.clear()
    for name, lat, lon in POINTS[route]:
        with st.container(border=True):
            st.markdown(f"#### 📍 {name}")
            try:
                data = fetch_weather(lat, lon)
                cur = data["current"]
                code = int(cur["weather_code"])
                hourly_data = data.get("hourly", {})
                visibility_value = None
                if hourly_data and cur.get("time") in hourly_data.get("time", []):
                    visibility_index = hourly_data["time"].index(cur["time"])
                    visibility_value = hourly_data.get("visibility", [None] * len(hourly_data["time"]))[visibility_index]
                x,y,z,w = st.columns(4)
                x.metric("Temperature", f'{cur.get("temperature_2m","—")} °C')
                y.metric("Feels like", f'{cur.get("apparent_temperature","—")} °C')
                z.metric("Wind", f'{cur.get("wind_speed_10m","—")} km/h')
                w.metric("Visibility", f'{(visibility_value/1000):.1f} km' if visibility_value is not None else "—")
                st.write(f"**موسم:** {weather_label(code)}  ·  **بارش:** {cur.get('precipitation','—')} mm  ·  **نمی:** {cur.get('relative_humidity_2m','—')}%")
                st.caption(f"API observation time: {cur.get('time','unknown')} • Source: Open-Meteo")
                hourly = data.get("hourly",{})
                if hourly:
                    df = pd.DataFrame({"Time":hourly["time"][:12],"Rain probability (%)":hourly.get("precipitation_probability",[])[:12],"Rain (mm)":hourly.get("precipitation",[])[:12]})
                    st.line_chart(df.set_index("Time"), height=170)
            except Exception as e:
                st.error(f"Weather service unavailable for {name}. Check internet and try again. Details: {e}")

elif page == "Driver Registry":
    st.subheader("Driver registration")
    with st.form("driver_form",clear_on_submit=True):
        name=st.text_input("Driver name")
        phone=st.text_input("Mobile number",placeholder="03XXXXXXXXX")
        vehicle=st.text_input("Vehicle registration")
        route=st.selectbox("Registered route",ROUTES)
        language=st.selectbox("Alert language",LANGUAGES)
        ok=st.form_submit_button("Register driver")
    if ok:
        if name.strip() and phone.strip() and vehicle.strip():
            run("INSERT INTO drivers(name,phone,vehicle,route,language,created_at) VALUES(?,?,?,?,?,?)",(name.strip(),phone.strip(),vehicle.strip(),route,language,datetime.now().isoformat(timespec="minutes")))
            st.success("Driver saved in local demo database.")
        else: st.error("All fields are required.")
    driver_data = pd.DataFrame(rows("SELECT id,name,phone,vehicle,route,language,created_at FROM drivers ORDER BY id DESC"))
    st.dataframe(driver_data,use_container_width=True,hide_index=True)
    st.download_button(
        "Download driver registry (CSV)",
        data=driver_data.to_csv(index=False).encode("utf-8-sig"),
        file_name="highway_watch_drivers.csv",
        mime="text/csv",
        disabled=driver_data.empty,
    )

elif page == "Road Status":
    st.subheader("Road status register")
    st.warning("No live government road-status feed is connected. Only authorized, verified operator updates should be entered here.")
    data=rows("SELECT * FROM road_status ORDER BY route,area")
    opts={f'{x["id"]} · {x["route"]} · {x["area"]}':x for x in data}
    choice=st.selectbox("Select road segment",list(opts))
    item=opts[choice]
    with st.form("road_form"):
        status=st.selectbox("Status",ROAD_STATUSES,index=ROAD_STATUSES.index(item["status"]) if item["status"] in ROAD_STATUSES else 0)
        note=st.text_input("Authority reference / operator note",value=item["authority_note"])
        save=st.form_submit_button("Save road status")
    if save:
        run("UPDATE road_status SET status=?,authority_note=?,updated_at=? WHERE id=?",(status,note,datetime.now().isoformat(timespec="minutes"),item["id"]))
        st.success("Road status saved.")
        st.rerun()
    st.dataframe(pd.DataFrame(rows("SELECT route,area,status,authority_note,updated_at FROM road_status")),use_container_width=True,hide_index=True)

elif page == "Checkpoints":
    st.subheader("Highway checkpoints")
    with st.form("cp_form",clear_on_submit=True):
        nm=st.text_input("Checkpoint name")
        rt=st.selectbox("Route",ROUTES)
        loc=st.text_input("Location")
        add=st.form_submit_button("Add checkpoint")
    if add:
        if nm.strip() and loc.strip():
            run("INSERT INTO checkpoints(name,route,location) VALUES(?,?,?)",(nm,rt,loc))
            st.success("Checkpoint added.")
        else: st.error("Enter checkpoint name and location.")
    st.dataframe(pd.DataFrame(rows("SELECT * FROM checkpoints ORDER BY id DESC")),use_container_width=True,hide_index=True)
    st.caption("Current checkpoint list includes virtual town-level demo points. Physical checkpoint installation and QR readers are not connected.")

elif page == "Alert Centre":
    st.subheader("Generate Urdu alert preview")
    drivers=rows("SELECT * FROM drivers ORDER BY id DESC")
    if not drivers:
        st.info("Register a driver first.")
    else:
        dmap={f'{x["name"]} | {x["phone"]} | {x["route"]}':x for x in drivers}
        d= dmap[st.selectbox("Driver",list(dmap))]
        segs=POINTS[d["route"]]
        area=st.selectbox("Route area", [x[0] for x in segs])
        roadrows=rows("SELECT * FROM road_status WHERE route=? AND area=?",(d["route"],area))
        road=roadrows[0]["status"] if roadrows else "Clearance Pending"
        st.info(f"Road status currently stored as: {road}. This is not independently verified.")
        message=alert_text(area,"موسم API se check karein",road)
        st.text_area("Urdu SMS draft",message,height=120)
        channel=st.radio("Delivery mode",["SMS preview only","Voice call preview only","SMS + voice preview"],horizontal=True)
        if st.button("Save demo alert",type="primary"):
            run("INSERT INTO alerts(driver_id,route,message,channel,status,created_at) VALUES(?,?,?,?,?,?)",(d["id"],d["route"],message,channel,"Preview only — not sent",datetime.now().isoformat(timespec="minutes")))
            st.success("Preview saved. No SMS or phone call was sent.")
            st.caption("Real delivery needs an approved SMS/voice provider, account credentials, consent and testing.")

elif page == "Alert History":
    data=rows("""SELECT alerts.id,drivers.name,drivers.phone,alerts.route,alerts.message,alerts.channel,alerts.status,alerts.created_at
    FROM alerts LEFT JOIN drivers ON drivers.id=alerts.driver_id ORDER BY alerts.id DESC""")
    if data:
        alert_data = pd.DataFrame(data)
        st.dataframe(alert_data,use_container_width=True,hide_index=True)
        st.download_button(
            "Download alert history (CSV)",
            data=alert_data.to_csv(index=False).encode("utf-8-sig"),
            file_name="highway_watch_alert_history.csv",
            mime="text/csv",
        )
    else:
        st.info("No alert previews yet.")

st.markdown("---")
st.caption("Weather provider: Open-Meteo (forecast, not official road clearance). Town coordinates are representative. This educational prototype is not an emergency service.")
