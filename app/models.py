from datetime import datetime

from sqlalchemy import Column, Integer, Float, DateTime

from app.database import Base


class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)

    wind_speed = Column(Float)
    wind_gust = Column(Float)
    wind_direction = Column(Float)
    pressure = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    dew_point = Column(Float)
    solar_radiation = Column(Float)
    uv_index = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)