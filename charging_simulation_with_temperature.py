
import json,time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

#Energy_price in Öre per kWh incl VAT
energy_price=[85.28,70.86,68.01,67.95,68.01,85.04,87.86,100.26,118.45,116.61,105.93,91.95,90.51,90.34,90.80,88.85,90.39,99.03,87.11,82.9,80.45,76.48,32.00,34.29]

#Residential building
max_power_residential_building=11  # (11 kW = 16A 3 phase)
base_load_residential_percent=[0.08,0.07,0.20,0.18,0.25,0.35,0.41,0.34,0.35,0.40,0.43,0.56,0.42,0.34,0.32,0.33,0.53,1.00,0.81,0.55,0.39,0.24,0.17,0.09]
base_load_residential_kwh=[value * max_power_residential_building for value in base_load_residential_percent]
base_load_residential_kwh = [round(x, 2) for x in base_load_residential_kwh]
base_current_load=base_load_residential_kwh[0]

#Battery (Citroen e_Berlingo M)
ev_batt_nominal_capacity=50 # kWh
ev_batt_max_capacity=46.3   # kWh
ev_batt_capacity_percent=20 #
ev_batt_capacity_kWh=ev_batt_capacity_percent/100*ev_batt_max_capacity
ev_batt_energy_consumption=226 #kWh per km = 2260 per swedish mil
ev_battery_charge_start_stopp=False

#Charging station
charging_station_info= {"Power":"7.4"} #EV version 2 charger
charging_power=7.4 # kW pchmax from car manufacturer

#time
sim_hour=0
sim_min=0
seconds_per_hour=4

# define a lock to synchronize access to the global variable
global_lock = threading.Lock()

app = Flask(__name__)
CORS(app)

def main_prg():
    global sim_hour
    global sim_min
    global ev_battery_charge_start_stopp
    global ev_batt_capacity_percent
    global ev_batt_capacity_kWh
    global ev_batt_max_capacity
    global base_current_load
    global seconds_per_hour
    while True:
        base_current_load=base_load_residential_kwh[sim_hour]
        for i in range(0,seconds_per_hour):
            if ev_battery_charge_start_stopp:
                # 🔥 Temperature Monitoring Logic
                voltage = 3.8  # Assume average cell voltage
                current = charging_power / voltage  # I = P/V
                R_int = 0.002  # Internal resistance in ohms
                delta_t = 1    # Time step in seconds
                T_ambient = 25  # Ambient temperature in °C

                T_battery = T_ambient + R_int * (current ** 2) * delta_t
                T_battery = round(T_battery, 2)
                if T_battery > 45:
                    ev_battery_charge_start_stopp = False
                    print("⚠️ Overtemperature warning – charging stopped at", T_battery, "°C")

                if ev_batt_capacity_percent <110.0:
                    ev_batt_capacity_kWh=ev_batt_capacity_kWh+charging_power/seconds_per_hour
                    ev_batt_capacity_kWh=round(ev_batt_capacity_kWh,2)
                    base_current_load=round(base_current_load+charging_power/seconds_per_hour,2)
                    ev_batt_capacity_percent=round(ev_batt_capacity_kWh/ev_batt_max_capacity*100,2)
            sim_min=int(round((60/seconds_per_hour*i)%60,0))
            time.sleep(1)
        sim_hour=(sim_hour+1)%24
        sim_min=0

# (rest of the original code omitted for brevity)
