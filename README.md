
# EV Charging Simulation

EV Charging Simulation is a Python-based project that simulates the behavior of an electric vehicle charging system connected to a household power grid. The system demonstrates intelligent charging strategies using REST-based client server communication.

The project is just for showcasing skills in backend development, simulation logic, REST APIs, and data analysis.

---

## Project Overview

The system consists of two main parts:

1. A Flask-based simulation server that emulates an EV charging station.
2. A Python client that interacts with the server and controls charging behavior.

The simulation runs on accelerated time, allowing long charging sessions to be tested quickly.

---

## Features

- Flask based REST API for EV charging simulation
- Client server architecture using HTTP requests
- Two intelligent charging strategies:
 - Load-based charging (based on household power usage)
  - Price-based charging (based on electricity price patterns)
- Simulated time progression (1 hour equals a few seconds)
- Battery state tracking and logging
- CSV and text-based log generation
- Charging curve visualization using plots

---

## Technology Stack

- Programming Language: Python
- Backend Framework: Flask
- HTTP Communication: requests
- Data Processing: pandas
- Visualization: matplotlib
- Runtime: Python 3.8 or higher

---

## Repository Structure

EV_charging_Simulation/
├── backend/
│   └── charging_simulation.py
├── main.py
├── server_api.py
├── battery_log.csv
├── charging_log.txt
├── battery_plot.png
└── README.md

---

## Installation and Setup

### Step 1: Clone the Repository

git clone https://github.com/Rupana84/EV_charging_Simulation.git  
cd EV_charging_Simulation

### Step 2: Install Dependencies

pip install flask requests pandas matplotlib

### Step 3: Start the Simulation Server

python backend/charging_simulation.py

### Step 4: Run the Client

Open a new terminal and run:

python main.py

Select the desired charging mode when prompted.

---

## Output Files

After running the simulation, the following files are generated:

- battery_log.csv  
  Contains time-based battery charge data and system states.

- charging_log.txt  
  Detailed charging and decision logs.

- battery_plot.png  
  Visual representation of battery charge progression.

---

## Use Cases

- Demonstrating EV charging logic and smart energy management
- Simulating grid-aware charging strategies
- Academic projects related to EV systems or energy optimization
- Portfolio demonstration for backend and simulation development

---

## Future Improvements

- Support for multiple vehicles
- Real-time dashboard or GUI
- Integration with live electricity pricing APIs
- Extended battery health and temperature modeling

---

## Author

Gurpreet Singh Rupana

---

## License

This project is open for educational and demonstration purposes.
