import json, time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

user_override = None  # None, "force_on", or "force_off"

# Battery temperature (°C)
T_battery = 25.0  # current battery temperature (°C)

# Energy prices for each hour (Öre per kWh incl. VAT)
energy_price = [
    85.28, 70.86, 68.01, 67.95, 68.01, 85.04, 87.86, 100.26,
    118.45, 116.61, 105.93, 91.95, 90.51, 90.34, 90.80, 88.85,
    90.39, 99.03, 87.11, 82.9, 80.45, 76.48, 32.00, 34.29
]

# Residential building max power (kW)
max_power_residential_building = 11  # (11 kW = 16A 3-phase)

# Base load as fraction of max power for each hour
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

base_current_load = base_load_residential_kwh[0]  # current load (kW)

# EV battery parameters (Citroen e-Berlingo M)
ev_batt_nominal_capacity = 50      # kWh (nominal)
ev_batt_max_capacity = 46.3        # kWh (usable)
ev_batt_capacity_percent = 20      # initial SoC (%)
ev_batt_capacity_kWh = ev_batt_capacity_percent / 100 * ev_batt_max_capacity
ev_batt_energy_consumption = 226   # Wh/km
ev_battery_charge_start_stopp = False  # charging flag

# Charging station parameters
charging_station_info = {"Power": "7.4"}  # charger info
charging_power = 7.4                      # kW max charging power

# Simulation time settings
sim_hour = 0
sim_min = 0
seconds_per_hour = 4  # 1 simulated hour = 4 real seconds

# Thread lock to protect shared state
global_lock = threading.Lock()

app = Flask(__name__)
CORS(app)  # allow cross-origin requests


def main_prg():
    """Main simulation loop running in background thread.

    This loop:
    - Updates the residential base load per simulated hour
    - Adds EV charging power when charging is active
    - Updates battery SoC (kWh + %) while respecting max usable capacity
    - Tracks a simple battery temperature estimate and stops charging if it
      exceeds a defined safety threshold
    """
    global sim_hour, sim_min
    global ev_battery_charge_start_stopp
    global ev_batt_capacity_percent, ev_batt_capacity_kWh, ev_batt_max_capacity
    global base_current_load, seconds_per_hour
    global T_battery, global_lock

    # Safety threshold for the simple temperature model (°C)
    max_safe_temp = 45.0

    while True:
        # Base load for current simulated hour
        with global_lock:
            base_current_load = base_load_residential_kwh[sim_hour]

        for i in range(seconds_per_hour):
            with global_lock:
                if ev_battery_charge_start_stopp:
                    # Temperature monitoring during charging
                    voltage = 3.8       # assumed average cell voltage (V)
                    current = charging_power / voltage  # I = P / V
                    R_int = 0.002       # internal resistance (ohms)
                    delta_t = 1         # time step (seconds)
                    T_ambient = 25      # ambient temperature (°C)

                    # Simple temperature model: T = Tamb + R * I^2 * dt
                    T_battery = T_ambient + R_int * (current ** 2) * delta_t
                    T_battery = round(T_battery, 2)

                    # Stop charging if battery exceeds safe temperature
                    if T_battery > max_safe_temp:
                        ev_battery_charge_start_stopp = False
                        print("⚠️ Overtemperature – charging stopped at", T_battery, "°C")

                    # Battery charging and SoC update
                    if ev_batt_capacity_percent < 110.0:
                        # increase stored energy (kWh) based on charger power
                        ev_batt_capacity_kWh += charging_power / seconds_per_hour
                        ev_batt_capacity_kWh = round(ev_batt_capacity_kWh, 2)

                        # update total current load in the building
                        base_current_load = round(
                            base_current_load + charging_power / seconds_per_hour,
                            2
                        )

                        # recalculate SoC in percent based on usable capacity
                        ev_batt_capacity_percent = round(
                            ev_batt_capacity_kWh / ev_batt_max_capacity * 100,
                            2
                        )

                # Update simulated minutes (0–59)
                sim_min = int(round((60 / seconds_per_hour * i) % 60, 0))

            # wait one real second
            time.sleep(1)

        # Advance simulated hour (0–23)
        with global_lock:
            sim_hour = (sim_hour + 1) % 24
            sim_min = 0


# (rest of the original code omitted for brevity)