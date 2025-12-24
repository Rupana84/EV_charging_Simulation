# 🔋 Battery Management Simulation Project

**Author**: Gurpreet Singh Rupana  
**Date**: 2025-06-07

---

## 📘 Overview

This project simulates the operation of an Electric Vehicle (EV) charging system connected to a household. It uses a simulated server (via Flask) that responds to JSON requests and allows a Python-based client application to manage battery charging intelligently based on two strategies:

- **Load-based Mode**: Charges when household load is below 11 kW.
- **Price-based Mode**: Charges when electricity price is among the lowest 8 hours of the day.

---

## Features Implemented

- REST API communication with a simulated EV charging station
- Discharges battery to 20% before simulation
- Supports both **load** and **price** based charging strategies
- Simulated time: 1 hour = 10 seconds
- Logs data in `charging_log.txt` (full terminal log) and `battery_log.csv` (summary table)
- Tracks:

* Simulated hour
* Base load
* Electricity price
* Battery % charge
* Charging status

  **CSV plot** of battery charge level over time  
  Daily statistics such as total charged hours

---

## Files

| File                     | Description                                  |
| ------------------------ | -------------------------------------------- |
| `main.py`                | Main terminal-based simulation client        |
| `server_api.py`          | Handles REST communication with server       |
| `charging_simulation.py` | Simulated charging server (Flask)            |
| `battery_log.csv`        | Summary of each hour's simulation data       |
| `charging_log.txt`       | Detailed terminal log of simulation          |
| `battery_plot.png`       | Line graph showing battery charge % over 24h |

---

## Results Summary (Last Simulation)

- **Total Charging Time**: 8 hours
- **Initial Battery %**: 20.00
- **Final Battery %**: 83.93

---

## Graph Example

Battery percentage increased during simulation. Refer to `battery_plot.png`.

> **Tip:** You can open `battery_log.csv` in Excel or Numbers for detailed filtering or analysis.

---

## How to Run

1. Run the simulated server (once):

```bash
python charging_simulation.py
```

2. In another terminal, run the client app:

```bash
python main.py
```

3. Choose your mode when prompted: `load` or `price`.

---

## Requirements

- Python 3.8+
- Flask (for `charging_simulation.py`)
- Requests
- Pandas
- Matplotlib

---

---
