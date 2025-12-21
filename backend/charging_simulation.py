# Written by Rikard Ed 2024-01-30
#
# charging_simulation.py
# EV charging simulation server (Flask) + background thread

import json
import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Lock

# User override mode:
# None        -> AUTO  (algorithm can start/stop charging)
# "force_on"  -> user forces charging ON
# "force_off" -> user forces charging OFF
user_override = None

# Energy prices for 24 hours (Öre/kWh)
energy_price = [
    85.28, 70.86, 68.01, 67.95, 68.01, 85.04, 87.86, 100.26,
    118.45, 116.61, 105.93, 91.95, 90.51, 90.34, 90.80, 88.85,
    90.39, 99.03, 87.11, 82.9, 80.45, 76.48, 32.00, 34.29
]

# Max power for the household (kW)
max_power_residential_building = 11  # (11 kW = 16A 3-phase)

# Base load as percentage of max power for each hour
base_load_residential_percent = [
    0.08, 0.07, 0.20, 0.18, 0.25, 0.35, 0.41, 0.34,
    0.35, 0.40, 0.43, 0.56, 0.42, 0.34, 0.32, 0.33,
    0.53, 1.00, 0.81, 0.55, 0.39, 0.24, 0.17, 0.09
]

# Convert base load to kW and round
base_load_residential_kwh = [
    round(value * max_power_residential_building, 2)
    for value in base_load_residential_percent
]

base_current_load = base_load_residential_kwh[0]  # current hourly load (kW)

# Battery model values (Citroën e-Berlingo M)
ev_batt_nominal_capacity = 50       # kWh nominal
ev_batt_max_capacity = 46.3         # kWh usable
ev_batt_capacity_percent = 20       # initial SoC (%)
ev_batt_capacity_kWh = ev_batt_capacity_percent / 100 * ev_batt_max_capacity
ev_batt_energy_consumption = 226    # Wh/km

# Charging flag (True = charging enabled)
ev_battery_charge_start_stopp = False

# Charger power (kW)
charging_station_info = {"Power": "7.4"}
charging_power = 7.4

# Simulation time tracking
sim_hour = 0
sim_min = 0
seconds_per_hour = 60  # 1 simulated hour = 60 real seconds

# Thread lock for shared values
global_lock = threading.Lock()

app = Flask(__name__)
# For local + demo hosting; tighten later by replacing "*" with your frontend origin
CORS(app, resources={r"/*": {"origins": "*"}})

# Optional in-memory log buffer (for future /log endpoint if you want)
simulation_log = []
log_lock = Lock()
simulation_running = False


def add_log(line: str):
    """Add one log line to buffer and still print to console."""
    global simulation_log
    with log_lock:
        simulation_log.append(line)
        # keep buffer small
        if len(simulation_log) > 500:
            simulation_log = simulation_log[-500:]
    print(line)


def main_prg():
    """
    Background simulation loop:
    - Updates base load and battery SoC
    - Simple temperature check during charging
    - Advances simulated time
    - Hard-clamps SoC at 100% and stops charging when full
    """
    global sim_hour, sim_min
    global ev_battery_charge_start_stopp
    global ev_batt_capacity_percent, ev_batt_capacity_kWh, ev_batt_max_capacity
    global base_current_load, seconds_per_hour

    while True:
        # Base load for this simulated hour
        with global_lock:
            base_current_load = base_load_residential_kwh[sim_hour]

        for i in range(seconds_per_hour):
            with global_lock:
                if ev_battery_charge_start_stopp:
                    # Temperature monitoring during charging (simple model)
                    voltage = 3.8                      # assumed average cell voltage (V)
                    current = charging_power / voltage # I = P / V
                    R_int = 0.002                      # internal resistance (ohms)
                    delta_t = 1                        # time step (s)
                    T_ambient = 25                     # ambient temperature (°C)

                    T_battery = T_ambient + R_int * (current ** 2) * delta_t
                    T_battery = round(T_battery, 2)

                    # Stop charging if battery exceeds safe temperature
                    if T_battery > 45:
                        ev_battery_charge_start_stopp = False
                        add_log(f"Overtemperature – charging stopped at {T_battery} °C")

                    # Battery charging and SoC update (with clamp)
                    if ev_battery_charge_start_stopp and ev_batt_capacity_percent < 100.0:
                        ev_batt_capacity_kWh += charging_power / seconds_per_hour

                        # Hard clamp at physical max capacity
                        if ev_batt_capacity_kWh >= ev_batt_max_capacity:
                            ev_batt_capacity_kWh = ev_batt_max_capacity
                            ev_batt_capacity_percent = 100.0
                            ev_battery_charge_start_stopp = False  # stop charging
                            add_log("Battery reached 100% – charging stopped automatically.")
                        else:
                            ev_batt_capacity_kWh = round(ev_batt_capacity_kWh, 2)
                            ev_batt_capacity_percent = round(
                                ev_batt_capacity_kWh / ev_batt_max_capacity * 100,
                                2,
                            )

                    # Current load including charger (kW)
                    base_current_load = round(
                        base_load_residential_kwh[sim_hour]
                        + (charging_power if ev_battery_charge_start_stopp else 0),
                        2,
                    )

                # Update simulated minutes (0–59)
                sim_min = int(round((60 / seconds_per_hour * i) % 60, 0))

            # One real second per step
            time.sleep(1)

        # Advance simulated hour (0–23)
        with global_lock:
            sim_hour = (sim_hour + 1) % 24
            sim_min = 0


# Default route – returns battery energy in kWh
@app.route("/")
def home():
    return json.dumps(ev_batt_capacity_kWh)


# Return system info (includes override)
@app.route("/info", methods=["GET"])
def station_info():
    with global_lock:
        info = {
            "sim_time_hour": sim_hour,
            "sim_time_min": sim_min,
            "base_current_load": base_current_load,
            "battery_capacity_kWh": ev_batt_capacity_kWh,
            "battery_max_capacity_kWh": ev_batt_max_capacity,
            "ev_battery_charge_start_stopp": ev_battery_charge_start_stopp,
            "battery_percent": ev_batt_capacity_percent,
            "user_override": user_override or "auto",
        }
    return json.dumps(info), {"Access-Control-Allow-Origin": "*"}


# Return base load list (24 hours)
@app.route("/baseload", methods=["GET"])
def base_load_info():
    return json.dumps(base_load_residential_kwh)


# Return price list (24 hours)
@app.route("/priceperhour", methods=["GET"])
def price_per_hour_info():
    return json.dumps(energy_price)


# Start/stop charging – respects user override
@app.route("/charge", methods=["POST", "GET"])
def charge_battery():
    global ev_battery_charge_start_stopp, user_override

    if request.method == "POST":
        try:
            json_input = request.json or {}
            start_charg = json_input.get("charging", 0)

            with global_lock:
                # If user override is active, ignore algorithm commands
                if user_override in ("force_on", "force_off"):
                    return json.dumps(
                        {
                            "charging": "on"
                            if ev_battery_charge_start_stopp
                            else "off",
                            "override": user_override,
                        }
                    )

                # Normal behaviour in AUTO mode
                if start_charg == "on":
                    ev_battery_charge_start_stopp = True
                    return json.dumps(
                        {"charging": "on", "override": user_override}
                    )
                if start_charg == "off":
                    ev_battery_charge_start_stopp = False
                    return json.dumps(
                        {"charging": "off", "override": user_override}
                    )

                return json.dumps({"error": "Invalid command"})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # GET returns battery % only
    with global_lock:
        percent = ev_batt_capacity_percent
    return jsonify(percent)


# Reset battery to 20% and restart simulation time (also clears override)
@app.route("/discharge", methods=["POST", "GET"])
def discharge_battery():
    global ev_battery_charge_start_stopp
    global base_current_load, ev_batt_capacity_percent
    global ev_batt_capacity_kWh, sim_hour, sim_min, user_override

    if request.method == "POST":
        json_input = request.json or {}
        discharg = json_input.get("discharging", 0)

        with global_lock:
            if discharg == "on":
                ev_battery_charge_start_stopp = False
                user_override = None  # back to AUTO mode
                base_current_load = base_load_residential_kwh[0]

                ev_batt_capacity_percent = 20
                ev_batt_capacity_kWh = (
                    ev_batt_capacity_percent / 100 * ev_batt_max_capacity
                )

                sim_hour = 0
                sim_min = 0

                return json.dumps({"discharging": "on"})

    return jsonify({"message": "Use POST to reset battery."})


# User override endpoint
@app.route("/override", methods=["GET", "POST"])
def override():
    """
    User override for charging:
    - GET  -> read current override + charging state
    - POST {"mode": "auto"}       -> clear override (AUTO)
    - POST {"mode": "force_on"}   -> force charging ON
    - POST {"mode": "force_off"}  -> force charging OFF
    """
    global user_override, ev_battery_charge_start_stopp

    if request.method == "GET":
        with global_lock:
            return (
                jsonify(
                    {
                        "override": user_override or "auto",
                        "charging": ev_battery_charge_start_stopp,
                    }
                ),
                200,
            )

    data = request.get_json(silent=True) or {}
    mode = data.get("mode")

    if mode not in ("auto", "force_on", "force_off"):
        return jsonify({"error": "Invalid mode"}), 400

    with global_lock:
        if mode == "auto":
            user_override = None
        else:
            user_override = mode

        # Apply immediate effect when forcing ON/OFF
        if user_override == "force_on":
            ev_battery_charge_start_stopp = True
        elif user_override == "force_off":
            ev_battery_charge_start_stopp = False

        result = {
            "override": user_override or "auto",
            "charging": ev_battery_charge_start_stopp,
        }

    return jsonify(result), 200


# Start background simulation thread
increment_sum_thread = threading.Thread(target=main_prg, daemon=True)
increment_sum_thread.start()

# Start Flask server
if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    # For DigitalOcean/App Platform this host/port is correct
    app.run(host="0.0.0.0", port=port)