
# SolarSystem Simulation

This module simulates a solar energy system, including PV production, battery storage behavior, and grid interaction. It is built for systems like the Studer *next3* and can be used for both basic and advanced simulations using time-series data.

## Features

- PV system modeling with orientation and slope
- Battery storage with efficiency and SOC tracking
- Inverter limits and grid export constraints
- Simulation of daily energy flow
- Cost evaluation based on grid usage and energy injection
- Visualizations using matplotlib

## Installation

Dependencies:
- Python 3.x
- pandas
- numpy
- matplotlib

Install dependencies with:

```bash
pip install pandas numpy matplotlib
```

## Getting Started

```python
from solarsystem import SolarSystem

# Create a new system
sys = SolarSystem(owner_name="Alice", adress="123 Solar Street")

# Load profiles from CSV
sys.load_csv_data_for_simulation("data.csv", "Load_kW", "Solar_kW", timestep=0.25)

# Run simulation
sys.run_storage_simulation()

# Display results
sys.display_storage_simulation()
```

## Class: SolarSystem

### Initialization

```python
SolarSystem(owner_name, adress)
```

### Key Attributes

- `pv_kW_installed`: PV installed capacity [kW]
- `batt_capacity_kWh`: Battery capacity [kWh]
- `soc_init`: Initial state of charge [%]
- `max_inverter_power`: Inverter max power [kW]
- `max_grid_injection_power`: Grid export limit [kW]

### Data Loading

- `load_csv_data_for_simulation(...)`: Load from CSV file
- `load_data_for_simulation(...)`: Load from arrays

### Simulations

- `run_simple_simulation()`: Simulation without battery
- `run_storage_simulation()`: Full system simulation with storage

### Visualizations

- `display_simple_simulation()`: Simple system plot
- `display_storage_simulation()`: Full system with battery plot
- `display_storage_energy()`: Battery energy graph
- `display_storage_debug()`: Debug visualization

## Economic Evaluation

### Function: `cost_function_economic(...)`

Estimate cost of grid usage and solar payback based on simulation results.

Parameters:
- `net_grid_simulation`: Power [kW]
- `delta_e_batt`: Battery energy change [kWh]
- `prices_consumption`: Buy price [€/kWh]
- `prices_injection`: Sell price [€/kWh]
- `timestep`: Step in hours

Returns: `[result_sim, balance_cost, cost_consumption, payback_injection]`

## License

TBD

## Author

Moix P-O  
Last updated: August 6, 2024
