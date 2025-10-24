🚌 Bus System Simulation

Overview

This simulation models a bus stop system using SimPy (a discrete-event simulation library in Python).
It simulates passenger arrivals, priorities, bus boarding, and departures to analyze system performance — including queue lengths, waiting times, bus utilization, and throughput.

⚙️ Requirements
Python Version

Python 3.6 or higher

Required Libraries

simpy – For discrete-event simulation

matplotlib – For generating visualizations

numpy – For numerical calculations

Usage Instructions

Run the simulation script in a terminal or IDE:

python bus_simulation.py


When executed, the script will prompt for simulation parameters with default values.

=== Bus System Simulation ===
Enter simulation parameters (press Enter for defaults):

Number of buses (default: 3):
Bus interval (seconds, default: 3600):
Passenger arrival rate (passengers/hour, default: 200):
Boarding time per passenger (seconds, default: 10):
Priority passenger probability (0 to 1, default: 0.2):
Simulation time (seconds, default: 3600):
Bus capacity (seats, default: 20):
Maximum stop time for boarding (seconds, default: 180):
Initial delay for first bus (seconds, default: 300):

Options

Press Enter to use all defaults
(e.g., 3 buses, 3600s interval, 200 passengers/hour, 10s boarding time)

Enter custom values for different scenarios
(e.g., 5 buses for higher capacity, 900s interval for frequent buses)

🧾 Example Console Output
=== Results for 3 Buses, 1800s Interval ===
Average wait time for Priority: 3.08 Minutes
Average wait time for Normal: 10.65 Minutes
Average queue length: 30.00 passengers
Average bus occupancy: 18.00 seats (90.00% utilization)
Throughput: 114.00 passengers/hour