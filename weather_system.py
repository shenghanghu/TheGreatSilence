"""Dynamic weather effects for communication simulation."""

from dataclasses import dataclass
from typing import Dict


WEATHER_ROTATION = ("clear", "cloudy", "rain", "storm", "solar_flare")


@dataclass(frozen=True)
class WeatherInfo:
    name: str
    description: str
    snr_penalty: float = 0.0
    laser_penalty: float = 0.0
    ber_multiplier: float = 1.0
    polar_boost: float = 0.0


class WeatherSystem:
    def __init__(self) -> None:
        self.weather_types: Dict[str, WeatherInfo] = {
            "clear": WeatherInfo("晴朗", "理想通信条件"),
            "cloudy": WeatherInfo("多云", "轻微信号衰减", snr_penalty=-1.0),
            "rain": WeatherInfo("降雨", "雨衰影响高频信号", snr_penalty=-3.0, laser_penalty=-8.0),
            "storm": WeatherInfo(
                "风暴",
                "强干扰，通信困难",
                snr_penalty=-6.0,
                laser_penalty=-15.0,
                ber_multiplier=1.5,
            ),
            "solar_flare": WeatherInfo(
                "太阳耀斑",
                "电离层扰动",
                snr_penalty=-4.0,
                polar_boost=2.0,
                ber_multiplier=1.15,
            ),
        }
        self.current_weather = "clear"

    def set_weather(self, weather_type: str) -> bool:
        if weather_type in self.weather_types:
            self.current_weather = weather_type
            return True
        return False

    def cycle_weather(self) -> str:
        idx = WEATHER_ROTATION.index(self.current_weather)
        next_weather = WEATHER_ROTATION[(idx + 1) % len(WEATHER_ROTATION)]
        self.current_weather = next_weather
        return next_weather

    def get_weather_info(self) -> WeatherInfo:
        return self.weather_types[self.current_weather]

    def apply_snr_effects(self, base_snr: float, coding: str, use_laser: bool = False) -> float:
        weather = self.get_weather_info()
        snr = float(base_snr) + weather.snr_penalty
        if use_laser:
            snr += weather.laser_penalty
        if coding and "Polar" in coding:
            snr += weather.polar_boost
        return snr

    def apply_ber_effects(self, base_ber: float, coding: str) -> float:
        weather = self.get_weather_info()
        ber = float(base_ber) * weather.ber_multiplier
        if coding and "Polar" in coding and weather.polar_boost > 0:
            ber *= 0.9
        return max(1e-7, min(0.5, ber))
