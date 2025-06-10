# charging_client/server_api.py

import requests  # For making HTTP requests to the simulated charging server

# Base URL of the Flask-based EV charging simulation server
BASE_URL = "http://127.0.0.1:5000"

def safe_json(response):
    """Safely parse JSON from a response or return fallback text/error.

    Handles:
    - 200 OK with valid JSON → returns parsed data
    - 200 OK but invalid JSON → returns warning with raw response
    - Any other HTTP status → returns error dict with status code and raw text
    """
    if response.status_code == 200:
        try:
            return response.json()
        except Exception:
            return {"warning": "Response was not valid JSON", "raw": response.text}
    else:
        return {"error": f"HTTP {response.status_code}", "raw": response.text}


def get_price_per_hour():
    """Fetch hourly electricity prices (öre/kWh) from the server."""
    response = requests.get(f"{BASE_URL}/priceperhour")
    data = safe_json(response)

    # If the server returns a list of 24 prices, return as-is
    if isinstance(data, list):
        return data

    # If the server returns a dict (e.g., {"0": 85.28, ...}), convert to list
    elif isinstance(data, dict):
        return [data[str(h)] for h in range(24)]

    else:
        raise ValueError("Unexpected response format from /priceperhour")


def get_baseload():
    """Fetch household base loads (kW) for each hour of the day."""
    response = requests.get(f"{BASE_URL}/baseload")
    data = safe_json(response)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data[str(h)] for h in range(24)]
    else:
        raise ValueError("Unexpected response format from /baseload")


def get_battery_percent():
    """Fetch current battery charge level (%) from the server."""
    response = requests.get(f"{BASE_URL}/charge")
    return safe_json(response)


def get_info():
    """Fetch detailed system info: battery %, current load, charging status, etc."""
    response = requests.get(f"{BASE_URL}/info")
    return safe_json(response)


def start_charging():
    """Send a POST request to the server to start charging the EV battery."""
    response = requests.post(f"{BASE_URL}/charge", json={"charging": "on"})
    return safe_json(response)


def stop_charging():
    """Send a POST request to the server to stop charging the EV battery."""
    response = requests.post(f"{BASE_URL}/charge", json={"charging": "off"})
    return safe_json(response)


def discharge_battery():
    """Send a POST request to reset/discharge the battery to 20% and restart simulation clock."""
    response = requests.post(f"{BASE_URL}/discharge", json={"discharging": "on"})
    return safe_json(response)