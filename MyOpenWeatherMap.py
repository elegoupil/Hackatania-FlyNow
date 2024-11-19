import requests
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, model_validator
from langchain_core.utils import get_from_dict_or_env


class OpenWeatherMapAPIWrapper(BaseModel):
    """Wrapper for OpenWeatherMap 5-day forecast API."""

    openweathermap_api_key: Optional[str] = None
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def validate_environment(cls, values: Dict) -> Any:
        """Validate that API key exists in environment."""
        openweathermap_api_key = get_from_dict_or_env(
            values, "openweathermap_api_key", "OPENWEATHERMAP_API_KEY"
        )
        values["openweathermap_api_key"] = openweathermap_api_key
        return values

    def _get_lat_lon(self, location: str) -> Optional[Dict[str, float]]:
        """Get latitude and longitude for a given location."""
        geocode_url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.openweathermap_api_key}"
        response = requests.get(geocode_url)
        if response.status_code == 200:
            data = response.json()
            return {
                "lat": data["coord"]["lat"],
                "lon": data["coord"]["lon"]
            }
        else:
            raise ValueError(f"Could not find the location: {location}")

    def _format_weather_info(self, location: str, forecast: Dict[str, Any]) -> str:
        """Format the forecast data into a human-readable string."""
        forecast_text = f"Weather forecast for {location}:\n"
        for entry in forecast["list"]:
            dt_txt = entry["dt_txt"]
            temp = entry["main"]["temp"]
            temp_min = entry["main"]["temp_min"]
            temp_max = entry["main"]["temp_max"]
            humidity = entry["main"]["humidity"]
            weather_description = entry["weather"][0]["description"]
            wind_speed = entry["wind"]["speed"]
            wind_deg = entry["wind"]["deg"]

            forecast_text += f"\n{dt_txt}:\n"
            forecast_text += f"  Temperature: {temp}°C (min: {temp_min}°C, max: {temp_max}°C)\n"
            forecast_text += f"  Weather: {weather_description}\n"
            forecast_text += f"  Wind: {wind_speed} m/s at {wind_deg}°\n"
            forecast_text += f"  Humidity: {humidity}%\n"
        return forecast_text

    def run(self, location: str) -> str:
        """Fetch the 5-day weather forecast for the given location."""
        # Get the latitude and longitude of the location
        lat_lon = self._get_lat_lon(location)

        # Fetch the 5-day forecast data using the latitude and longitude
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat_lon['lat']}&lon={lat_lon['lon']}&appid={self.openweathermap_api_key}&units=metric"
        response = requests.get(forecast_url)

        if response.status_code == 200:
            forecast_data = response.json()
            return self._format_weather_info(location, forecast_data)
        else:
            raise ValueError(f"Failed to retrieve forecast data for {location}.")