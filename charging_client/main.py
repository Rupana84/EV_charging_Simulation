import sys
import time
import csv
from datetime import datetime
from server_api import (
    get_price_per_hour,
    get_baseload,
    get_battery_percent,
    start_charging,
    stop_charging,
    discharge_battery,
    get_info
)

SECONDS_PER_HOUR = 2
MAX_HOURS = 24
BATTERY_CAPACITY_KWH = 46.3

# File paths
LOG_FILE = "simulation_log.txt"
CSV_FILE = "battery_log.csv"

def log_to_file(message: str):
    """Append a timestamped message to the log file."""
    with open(LOG_FILE, "a") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {message}\n")

def init_csv():
    """Create or overwrite the CSV file and write header."""
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Hour", "Base Load (kW)", "Price (öre)", "Battery (%)", "Charging"])

def append_csv_row(hour, base_load, price, battery_percent, charging):
    """Append a row to the CSV log."""
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([hour, base_load, price, battery_percent, charging])

def main():
    # Ask user for mode
    mode = input("\nSelect mode (load/price): ").strip().lower()
    if mode not in ["load", "price"]:
        print("❌ Invalid mode. Defaulting to 'load'.")
        mode = "load"

    print(f"\n🔋 Starting Battery Management Simulation in {mode.upper()} mode...\n")
    log_to_file(f"Simulation started in {mode.upper()} mode")

    discharge_battery()
    print("⏮️  Discharging battery to 20%...")
    log_to_file("Battery discharged to 20%")
    time.sleep(1)

    prices = get_price_per_hour()
    loads = get_baseload()
    print("✅ Loaded electricity prices and base loads for 24h.\n")
    log_to_file("Prices and base loads loaded")

    if mode == "price":
        cheapest_hours = sorted(range(MAX_HOURS), key=lambda h: prices[h])[:8]
        log_to_file(f"Cheapest hours (price mode): {cheapest_hours}")
    else:
        cheapest_hours = []

    init_csv()

    for hour in range(MAX_HOURS):
        info = get_info()
        battery_percent = info.get("battery_capacity_kWh", 0) / BATTERY_CAPACITY_KWH * 100
        charging = info.get("ev_battery_charge_start_stopp", False)
        base_load = loads[hour]
        price = prices[hour]

        should_charge = False
        if base_load < 11:
            if mode == "load":
                should_charge = battery_percent < 80
            elif hour in cheapest_hours:
                should_charge = battery_percent < 80

        if should_charge and not charging:
            start_charging()
            print("✅ Starting charging...")
            log_to_file(f"Hour {hour:02d}: Charging started")
        elif not should_charge and charging:
            stop_charging()
            print("⛔ Stopping charging...")
            log_to_file(f"Hour {hour:02d}: Charging stopped")

        print(f"\n🕒 Simulated Time: Hour {hour:02d}:00")
        print(f"⚡ Base Load: {base_load:.2f} kW | 💰 Price: {price:.2f} öre | "
              f"🔋 Battery: {battery_percent:.2f}% | 🚗 Charging: {charging}")

        log_to_file(f"Hour {hour:02d} → Load: {base_load:.2f} kW, Price: {price:.2f}, "
                    f"Battery: {battery_percent:.2f}%, Charging: {charging}")

        append_csv_row(hour, base_load, price, battery_percent, charging)

        time.sleep(SECONDS_PER_HOUR)

    final = get_battery_percent()
    print(f"\n🔚 Final Battery Charge: {final:.2f}%")
    log_to_file(f"Final Battery Charge: {final:.2f}%")
    log_to_file("Simulation completed.\n")

if __name__ == "__main__":
    main()