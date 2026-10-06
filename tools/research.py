import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")



def serper_search(query: str, num_results: int = 5) -> dict:
    if not SERPER_API_KEY:
        raise RuntimeError(
            "SERPER_API_KEY is missing. Add it to the environment."
        )

    response = requests.post(
        "https://google.serper.dev/search",
        headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json",
        },
        json={"q": query, "num": num_results},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def simplify_serper_results(data: dict):
    return [
        {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in data.get("organic", [])
    ]


def geocode_place(place: str):
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": place, "format": "jsonv2", "limit": 1},
        headers={"User-Agent": "AI-Travel-Planner-Web/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    if not data:
        return {"query": place, "found": False}

    item = data[0]
    return {
        "query": place,
        "found": True,
        "display_name": item.get("display_name", ""),
        "latitude": float(item["lat"]),
        "longitude": float(item["lon"]),
    }


def get_weather(latitude: float, longitude: float):
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "daily": ",".join([
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
            ]),
            "forecast_days": 16,
            "timezone": "auto",
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    daily = data.get("daily", {})

    return {
        "timezone": data.get("timezone"),
        "time": daily.get("time", []),
        "weather_code": daily.get("weather_code", []),
        "temperature_max": daily.get("temperature_2m_max", []),
        "temperature_min": daily.get("temperature_2m_min", []),
        "precipitation_probability": daily.get(
            "precipitation_probability_max", []
        ),
    }


def wikipedia_summary(place: str):
    title = place.strip().replace(" ", "_")
    response = requests.get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}",
        headers={"User-Agent": "AI-Travel-Planner-Web/1.0"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "title": data.get("title"),
        "extract": data.get("extract"),
        "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
    }


def get_route(origin_lat, origin_lon, destination_lat, destination_lon):
    coordinates = (
        f"{origin_lon},{origin_lat};"
        f"{destination_lon},{destination_lat}"
    )
    response = requests.get(
        f"https://router.project-osrm.org/route/v1/driving/{coordinates}",
        params={"overview": "false", "alternatives": "false"},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        return {"found": False}

    route = data["routes"][0]
    return {
        "found": True,
        "distance_km": round(route["distance"] / 1000, 2),
        "duration_hours": round(route["duration"] / 3600, 2),
    }


def get_exchange_rate(base_currency: str, target_currency: str):
    base = base_currency.upper()
    target = target_currency.upper()

    if base == target:
        return {"base": base, "target": target, "rate": 1.0}

    response = requests.get(
        "https://api.frankfurter.app/latest",
        params={"from": base, "to": target},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    return {
        "base": base,
        "target": target,
        "rate": data.get("rates", {}).get(target),
        "date": data.get("date"),
    }


def specialized_research(state):
    origin = state["origin"]
    destination = state["destination"]
    currency = state.get("currency", "INR").upper()

    origin_location = geocode_place(origin)
    destination_location = geocode_place(destination)

    if not origin_location.get("found"):
        raise ValueError(f"Could not geocode origin: {origin}")
    if not destination_location.get("found"):
        raise ValueError(f"Could not geocode destination: {destination}")

    olat, olon = origin_location["latitude"], origin_location["longitude"]
    dlat, dlon = destination_location["latitude"], destination_location["longitude"]

    currency_map = {
        "Dubai": "AED",
        "Abu Dhabi": "AED",
        "London": "GBP",
        "New York": "USD",
        "Paris": "EUR",
        "Rome": "EUR",
        "Berlin": "EUR",
        "Tokyo": "JPY",
    }
    target_currency = currency_map.get(destination, currency)

    tasks = {
        "weather": lambda: get_weather(dlat, dlon),
        "wikipedia": lambda: wikipedia_summary(destination),
        "route": lambda: get_route(olat, olon, dlat, dlon),
        "exchange_rate": lambda: get_exchange_rate(currency, target_currency),
    }

    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as exc:
                results[name] = {"error": str(exc)}

    interests = ", ".join(state.get("interests", []))
    queries = [
        f"best tourist attractions in {destination}",
        f"best hotels in {destination}",
        f"best restaurants in {destination}",
        f"best things to do in {destination} for {interests}",
        f"{destination} travel tips tourist guide",
    ]

    web_results = []
    for query in queries:
        try:
            web_results.append({
                "query": query,
                "results": simplify_serper_results(serper_search(query)),
            })
        except Exception as exc:
            web_results.append({
                "query": query,
                "results": [],
                "error": str(exc),
            })

    results["serper"] = web_results

    return {
        **state,
        "origin_location": origin_location,
        "destination_location": destination_location,
        "weather": results.get("weather", {}),
        "wikipedia": results.get("wikipedia", {}),
        "route": results.get("route", {}),
        "exchange_rate": results.get("exchange_rate", {}),
        "search_results": web_results,
        "phase2_research": results,
    }


def format_research(state) -> str:
    return "\n".join([
        "=== GEOCODING ===",
        json.dumps({
            "origin": state.get("origin_location"),
            "destination": state.get("destination_location"),
        }, indent=2),
        "\n=== WEATHER ===",
        json.dumps(state.get("weather", {}), indent=2),
        "\n=== WIKIPEDIA ===",
        json.dumps(state.get("wikipedia", {}), indent=2),
        "\n=== ROUTE ===",
        json.dumps(state.get("route", {}), indent=2),
        "\n=== EXCHANGE RATE ===",
        json.dumps(state.get("exchange_rate", {}), indent=2),
        "\n=== WEB SEARCH ===",
        json.dumps(state.get("search_results", []), indent=2),
    ])
