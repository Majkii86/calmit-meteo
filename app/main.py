import time
from pathlib import Path
from datetime import datetime, timedelta, time as dt_time, date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, SessionLocal
from app.models import WeatherData

BASE_DIR = Path(__file__).resolve().parent.parent

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

latest_weather = {}
last_update_ts = 0
last_update_dt = None
last_cleanup_date = None
WRITE_TOKEN = "CsK258963"


FIELD_MAP = {
    "field1": "wind_speed",
    "field2": "wind_gust",
    "field3": "wind_direction",
    "field4": "pressure",
    "field5": "temperature",
    "field6": "humidity",
    "field7": "dew_point",
    "field8": "solar_radiation",
    "field9": "uv_index",
}


def wind_direction_text(deg):
    if deg is None:
        return ""

    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(deg / 45) % 8
    return directions[index]


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "templates" / "index.html")


def cleanup_old_records_if_needed():
    global last_cleanup_date

    today = date.today()

    if last_cleanup_date == today:
        return

    older_than = datetime.now() - timedelta(days=365)

    db = SessionLocal()

    try:
        deleted = (
            db.query(WeatherData)
            .filter(WeatherData.created_at < older_than)
            .delete()
        )
        db.commit()

        if deleted:
            print(f"Cleanup DB: deleted {deleted} old records")

        last_cleanup_date = today

    except Exception as e:
        print("Cleanup DB error:", e)

    finally:
        db.close()


@app.get("/data")
def receive_data(request: Request):
    global latest_weather, last_update_ts, last_update_dt

    token = request.query_params.get("t")

    if token != WRITE_TOKEN:
        return JSONResponse(
            {"status": "forbidden"},
            status_code=403
        )

   
    parsed = {}

    for key, value in request.query_params.items():
        if key in FIELD_MAP:
            try:
                parsed[FIELD_MAP[key]] = round(float(value), 1)
            except ValueError:
                pass

    latest_weather = parsed
    last_update_ts = time.time()
    last_update_dt = datetime.now()

    db = SessionLocal()

    try:
        row = WeatherData(**parsed)
        db.add(row)
        db.commit()
    finally:
        db.close()

    cleanup_old_records_if_needed()    

    return JSONResponse({"status": "ok"})


@app.get("/api/current")
def current():
    age = time.time() - last_update_ts if last_update_ts else None
    wind_direction = latest_weather.get("wind_direction")

    return {
        **latest_weather,
        "wind_direction_text": wind_direction_text(wind_direction),
        "online": age is not None and age < 90,
        "age_seconds": int(age) if age is not None else None,
        "last_update": last_update_dt.strftime("%d.%m.%Y %H:%M:%S") if last_update_dt else None,
    }


@app.get("/api/history")
def history():
    since = datetime.now() - timedelta(hours=24)

    db = SessionLocal()

    try:
        rows = (
            db.query(WeatherData)
            .filter(WeatherData.created_at >= since)
            .order_by(WeatherData.created_at.asc())
            .all()
        )
    finally:
        db.close()

    return [
        {
            "temperature": row.temperature,
            "humidity": row.humidity,
            "wind_speed": row.wind_speed,
            "pressure": row.pressure,
            "created_at": row.created_at.strftime("%H:%M"),
        }
        for row in rows
    ]


@app.get("/api/today")
def today_stats():
    start_of_day = datetime.combine(datetime.now().date(), dt_time.min)

    db = SessionLocal()

    try:
        rows = (
            db.query(WeatherData)
            .filter(WeatherData.created_at >= start_of_day)
            .all()
        )
    finally:
        db.close()

    temperatures = [r.temperature for r in rows if r.temperature is not None]
    wind_speeds = [r.wind_speed for r in rows if r.wind_speed is not None]
    wind_gusts = [r.wind_gust for r in rows if r.wind_gust is not None]
    uv_values = [r.uv_index for r in rows if r.uv_index is not None]

    return {
        "records_today": len(rows),
        "temperature_min": round(min(temperatures), 1) if temperatures else None,
        "temperature_max": round(max(temperatures), 1) if temperatures else None,
        "wind_speed_max": round(max(wind_speeds), 1) if wind_speeds else None,
        "wind_gust_max": round(max(wind_gusts), 1) if wind_gusts else None,
        "uv_max": round(max(uv_values), 1) if uv_values else None,
    }


@app.get("/api/status")
def api_status():
    age = time.time() - last_update_ts if last_update_ts else None
    start_of_day = datetime.combine(datetime.now().date(), dt_time.min)

    db_ok = True
    records_today = 0

    db = SessionLocal()

    try:
        records_today = (
            db.query(WeatherData)
            .filter(WeatherData.created_at >= start_of_day)
            .count()
        )
    except Exception:
        db_ok = False
    finally:
        db.close()

    return {
        "weather_online": age is not None and age < 90,
        "age_seconds": int(age) if age is not None else None,
        "last_update": last_update_dt.strftime("%d.%m.%Y %H:%M:%S") if last_update_dt else None,
        "database_ok": db_ok,
        "records_today": records_today,
    }


@app.post("/api/cleanup")
def cleanup_database(request: Request):
    token = request.query_params.get("token")

    if token != WRITE_TOKEN:
        return JSONResponse(
            {"status": "forbidden"},
            status_code=403
        )

    older_than = datetime.now() - timedelta(days=365)

    db = SessionLocal()

    try:
        deleted = (
            db.query(WeatherData)
            .filter(WeatherData.created_at < older_than)
            .delete()
        )
        db.commit()
    finally:
        db.close()

    return {
        "status": "ok",
        "deleted_rows": deleted
    }