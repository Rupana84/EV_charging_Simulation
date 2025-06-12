import requests  # Library used to send HTTP requests to the Flask simulation server

# Base URL where the Flask-based EV charging simulation server is running
BASE_URL = "http://127.0.0.1:5000"

def safe_json(response):
    """
    Response or return fallback message.
    Handles:
    - Valid JSON responses (status 200)
    - Error status codes
    """
    if response.status_code == 200:
        try:
            return response.json()  # Try to parse the response as JSON
        except Exception:
            # Return raw response if JSON parsing fails
            return {"warning": "Response was not valid JSON", "raw": response.text}
    else:
        # Return error if response code is not 200
        return {"error": f"HTTP {response.status_code}", "raw": response.text}


def get_price_per_hour():
    """
    Get electricity prices for each hour of the day from the server.
    Tries to parse as a list or convert dict to list.
    """
    response = requests.get(f"{BASE_URL}/priceperhour")  # Send GET request to server
    data = safe_json(response)  # Parse response safely

    if isinstance(data, list):
        return data  # Return list directly if it is already a list

    elif isinstance(data, dict):
        # Convert dictionary values to list by an hour key
        return [data[str(h)] for h in range(24)]

    else:
        raise ValueError("Unexpected response format from /priceperhour")


def get_baseload():
    """
    Get household base load values for each hour of the day.
    Returns list of 24 values representing hourly kW usage.
    """
    response = requests.get(f"{BASE_URL}/baseload")  # GET request to /baseload
    data = safe_json(response)

    if isinstance(data, list):
        return data  # Return list if server gave a list

    elif isinstance(data, dict):
        # Convert dictionary to list assuming keys "0" to "23"
        return [data[str(h)] for h in range(24)]

    else:
        raise ValueError("Unexpected response format from /baseload")


def get_battery_percent():
    """
    Get the current battery charge in percent.
    Used for real-time battery status monitoring.
    """
    response = requests.get(f"{BASE_URL}/charge")  # GET request to /charge returns battery %
    return safe_json(response)  # Return parsed response


def get_info():
    """
    Get detailed system info from the simulation:
    Includes battery %, base load, time, and charging status.
    """
    response = requests.get(f"{BASE_URL}/info")  # GET request to /info
    return safe_json(response)


def start_charging():
    """
    Send a POST request to the server to start EV battery charging.
    Tells the Flask server to turn on charging.
    """
    response = requests.post(f"{BASE_URL}/charge", json={"charging": "on"})  # POST with 'on'
    return safe_json(response)


def stop_charging():
    """
    Send a POST request to stop EV battery charging.
    Tells the Flask server to stop charging activity.
    """
    response = requests.post(f"{BASE_URL}/charge", json={"charging": "off"})  # POST with 'off'
    return safe_json(response)


def discharge_battery():
    """
    Reset or discharge the battery to 20% to begin simulation.
    Also resets the simulated clock back to hour 0.
    """
    response = requests.post(f"{BASE_URL}/discharge", json={"discharging": "on"})  # POST to reset
    return safe_json(response)