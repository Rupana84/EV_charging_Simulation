# Import necessary libraries
import sys
import time
import csv
from datetime import datetime

# Import helper functions from your Flask API wrapper
from server_api import (
    get_price_per_hour,        # Gets hourly electricity price
    get_baseload,              # Gets hourly household base load
    get_battery_percent,       # Gets current battery percentage
    start_charging,            # Sends command to start charging
    stop_charging,             # Sends command to stop charging
    discharge_battery,         # Resets battery to 20%
    get_info                   # Gets full system info from /info
)

# Time control: 1 hour in simulation = 2 seconds in real time
SECONDS_PER_HOUR = 2
MAX_HOURS = 24                        # Total simulation hours
BATTERY_CAPACITY_KWH = 46.3           # Battery capacity in kWh

# Log file paths
LOG_FILE = "simulation_log.txt"
CSV_FILE = "battery_log.csv"

# Function: Write log entry to .txt file with timestamp
def log_to_file(message: str):
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

# Function: Initialize CSV file with headers
def init_csv():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Hour", "Base Load (kW)", "Price (öre)", "Battery (%)", "Charging"])

# Function: Append one row of data to the CSV
def append_csv_row(hour, base_load, price, battery_percent, charging):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([hour, base_load, price, battery_percent, charging])

# MAIN FUNCTION: Runs the battery charging simulation
def main():
    # Ask user to select simulation mode: 'load' or 'price'
    mode = input("\nSelect mode (load/price): ").strip().lower()
    if mode not in ["load", "price"]:
        print("❌ Invalid mode. Defaulting to 'load'.")
        mode = "load"

    print(f"\n🔋 Starting Battery Management Simulation in {mode.upper()} mode...\n")
    log_to_file(f"Simulation started in {mode.upper()} mode")

    # Discharge the battery to 20% before starting the simulation
    discharge_battery()
    print("⏮️  Discharging battery to 20%...")
    log_to_file("Battery discharged to 20%")
    time.sleep(1)

    # Load prices and base loads from the server
    prices = get_price_per_hour()
    loads = get_baseload()
    print("✅ Loaded electricity prices and base loads for 24h.\n")
    log_to_file("Prices and base loads loaded")

    # If price mode, find the 8 cheapest hours for charging
    if mode == "price":
        cheapest_hours = sorted(range(MAX_HOURS), key=lambda h: prices[h])[:8]
        log_to_file(f"Cheapest hours (price mode): {cheapest_hours}")
    else:
        cheapest_hours = []

    # Create new CSV file
    init_csv()

    # Loop through each simulated hour
    for hour in range(MAX_HOURS):
        # Get latest system info from the API
        info = get_info()
        battery_percent = info.get("battery_capacity_kWh", 0) / BATTERY_CAPACITY_KWH * 100
        charging = info.get("ev_battery_charge_start_stopp", False)
        base_load = loads[hour]
        price = prices[hour]

        # Decide whether to charge based on mode and conditions
        should_charge = False
        if base_load < 11:  # Household load limit (kW)
            if mode == "load":
                should_charge = battery_percent < 80
            elif hour in cheapest_hours:
                should_charge = battery_percent < 80

        # If we should charge and aren't yet charging, start charging
        if should_charge and not charging:
            start_charging()
            print("✅ Starting charging...")
            log_to_file(f"Hour {hour:02d}: Charging started")
            time.sleep(1)               # Let the server loop process it
            info = get_info()           # Re-fetch updated values
            charging = info.get("ev_battery_charge_start_stopp", False)

        # If we should stop charging and are currently charging, stop charging
        elif not should_charge and charging:
            stop_charging()
            print("⛔ Stopping charging...")
            log_to_file(f"Hour {hour:02d}: Charging stopped")
            time.sleep(1)               # Let the server loop process it
            info = get_info()           # Re-fetch updated values
            charging = info.get("ev_battery_charge_start_stopp", False)

        # Print status for the current hour
        print(f"\n🕒 Simulated Time: Hour {hour:02d}:00")
        print(f"⚡ Base Load: {base_load:.2f} kW | 💰 Price: {price:.2f} öre | "
              f"🔋 Battery: {battery_percent:.2f}% | 🚗 Charging: {charging}")

        # Log this hour’s details
        log_to_file(f"Hour {hour:02d} → Load: {base_load:.2f} kW, Price: {price:.2f}, "
                    f"Battery: {battery_percent:.2f}%, Charging: {charging}")

        # Save row to CSV
        append_csv_row(hour, base_load, price, battery_percent, charging)

        # Wait for the simulated hour to pass (2 seconds)
        time.sleep(SECONDS_PER_HOUR)

    # Final battery status
    final = get_battery_percent()
    print(f"\n🔚 Final Battery Charge: {final:.2f}%")
    log_to_file(f"Final Battery Charge: {final:.2f}%")
    log_to_file("Simulation completed.\n")

# Only run if the file is executed directly (not imported)
if __name__ == "__main__":
    main()