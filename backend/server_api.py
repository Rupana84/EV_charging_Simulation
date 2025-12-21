import requests  # Send HTTP requests to the Flask simulation server

# Base URL of the EV simulation server
BASE_URL = "http://127.0.0.1:5000"


def safe_json(response):
    """Parse JSON safely and return structured errors."""
    if response.status_code == 200:
        try:
            return response.json()          # Try to parse JSON body
        except Exception:
            return {"warning": "Invalid JSON", "raw": response.text}
    # Non-200 -> return an error structure
    return {"error": f"HTTP {response.status_code}", "raw": response.text}


# ------------------------------
# PRICE & BASELOAD
# ------------------------------

def get_price_per_hour():
    """Fetch hourly electricity prices (24 values)."""
    response = requests.get(f"{BASE_URL}/priceperhour")  # Call Flask /priceperhour
    data = safe_json(response)

    if isinstance(data, list):
        return data                                      # Already a list
    elif isinstance(data, dict):
        # Convert dict with hour keys "0"–"23" to a list
        return [data[str(h)] for h in range(24)]
    else:
        raise ValueError("Unexpected price format")


def get_baseload():
    """Fetch household base load for 24 hours."""
    response = requests.get(f"{BASE_URL}/baseload")      # Call Flask /baseload
    data = safe_json(response)

    if isinstance(data, list):
        return data                                      # Already a list
    elif isinstance(data, dict):
        # Convert dict with hour keys "0"–"23" to a list
        return [data[str(h)] for h in range(24)]
    else:
        raise ValueError("Unexpected baseload format")


# ------------------------------
# BATTERY + INFO
# ------------------------------

def get_battery_percent():
    """Fetch current battery state of charge (%)."""
    response = requests.get(f"{BASE_URL}/charge")        # GET /charge returns % value
    return safe_json(response)


def get_info():
    """
    Fetch system info:
    sim time, base load, battery kWh, charging flag, and override mode.
    """
    response = requests.get(f"{BASE_URL}/info")          # GET /info
    return safe_json(response)


# ------------------------------
# CHARGING CONTROL
# ------------------------------

def start_charging():
    """Ask server to turn charging ON (ignored if override is force_on/force_off)."""
    response = requests.post(
        f"{BASE_URL}/charge",
        json={"charging": "on"}                          # POST body: turn on
    )
    return safe_json(response)


def stop_charging():
    """Ask server to turn charging OFF (ignored if override is force_on/force_off)."""
    response = requests.post(
        f"{BASE_URL}/charge",
        json={"charging": "off"}                         # POST body: turn off
    )
    return safe_json(response)


def discharge_battery():
    """Reset battery to 20% and reset simulated clock to hour 0."""
    response = requests.post(
        f"{BASE_URL}/discharge",
        json={"discharging": "on"}                       # POST body: trigger reset
    )
    return safe_json(response)


# ------------------------------
# USER OVERRIDE CONTROL
# ------------------------------

def get_override():
    """Check current override mode and charging state."""
    response = requests.get(f"{BASE_URL}/override")      # GET /override
    return safe_json(response)


def set_override(mode):
    """
    Set override mode on the server.

    mode must be one of:
      - "auto"       -> algorithm controls charging
      - "force_on"   -> user forces charging ON
      - "force_off"  -> user forces charging OFF
    """
    response = requests.post(
        f"{BASE_URL}/override",
        json={"mode": mode}                              # POST body: new mode
    )
    return safe_json(response)