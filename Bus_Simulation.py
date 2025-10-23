import simpy
import random
import heapq
import os

# Get user input with validation for simulation parameters.
def get_user_input():
    print("=== Bus System Simulation ===")
    print("Enter simulation parameters (press Enter for defaults):")
    
    num_buses = input("Number of buses (default: 3): ") or 3
    try:
        num_buses = int(num_buses)
        if num_buses <= 0:
            raise ValueError("Number of buses must be positive")
    except ValueError:
        print("Invalid input, using default: 3 buses")
        num_buses = 3
    
    bus_interval = input("Bus interval (seconds, default: 3600): ") or 3600
    try:
        bus_interval = float(bus_interval)
        if bus_interval <= 0:
            raise ValueError("Bus interval must be positive")
    except ValueError:
        print("Invalid input, using default: 3600 seconds")
        bus_interval = 3600
    
    passenger_rate = input("Passenger arrival rate (passengers/hour, default: 200): ") or 200
    try:
        passenger_rate = float(passenger_rate)
        if passenger_rate <= 0:
            raise ValueError("Passenger rate must be positive")
    except ValueError:
        print("Invalid input, using default: 200 passengers/hour")
        passenger_rate = 200
    
    boarding_time = input("Boarding time per passenger (seconds, default: 10): ") or 10
    try:
        boarding_time = float(boarding_time)
        if boarding_time <= 0:
            raise ValueError("Boarding time must be positive")
    except ValueError:
        print("Invalid input, using default: 10 seconds")
        boarding_time = 10
    
    priority_prob = input("Priority passenger probability (0 to 1, default: 0.2): ") or 0.2
    try:
        priority_prob = float(priority_prob)
        if not 0 <= priority_prob <= 1:
            raise ValueError("Probability must be between 0 and 1")
    except ValueError:
        print("Invalid input, using default: 0.2")
        priority_prob = 0.2
    
    sim_time = input("Simulation time (seconds, default: 3600): ") or 3600
    try:
        sim_time = float(sim_time)
        if sim_time <= 0:
            raise ValueError("Simulation time must be positive")
    except ValueError:
        print("Invalid input, using default: 3600 seconds")
        sim_time = 3600
    
    bus_capacity = input("Bus capacity (seats, default: 20): ") or 20
    try:
        bus_capacity = int(bus_capacity)
        if bus_capacity <= 0:
            raise ValueError("Bus capacity must be positive")
    except ValueError:
        print("Invalid input, using default: 20 seats")
        bus_capacity = 20
    
    max_stop_time = input("Maximum stop time for boarding (seconds, default: 180): ") or 180
    try:
        max_stop_time = float(max_stop_time)
        if max_stop_time <= 0:
            raise ValueError("Maximum stop time must be positive")
    except ValueError:
        print("Invalid input, using default: 180 seconds")
        max_stop_time = 180
    
    initial_bus_delay = input("Initial delay for first bus (seconds, default: 300): ") or 300
    try:
        initial_bus_delay = float(initial_bus_delay)
        if initial_bus_delay < 0:
            raise ValueError("Initial bus delay must be non-negative")
    except ValueError:
        print("Invalid input, using default: 300 seconds")
        initial_bus_delay = 300
    
    # Return a dictionary of validated parameters used by the simulator.
    return {
        'NUM_BUSES': num_buses,
        'BUS_INTERVAL': bus_interval,
        'PASSENGER_ARRIVAL_RATE': passenger_rate,
        'BOARDING_TIME': boarding_time,
        'PRIORITY_PROB': priority_prob,
        'SIM_TIME': sim_time,
        'BUS_CAPACITY': bus_capacity,
        'MAX_STOP_TIME': max_stop_time,
        'INITIAL_BUS_DELAY': initial_bus_delay
    }

def run_simulation(params):
    # Extract parameters for readability inside the simulation functions.
    PASSENGER_ARRIVAL_RATE = params['PASSENGER_ARRIVAL_RATE']
    BUS_INTERVAL = params['BUS_INTERVAL']
    BUS_CAPACITY = params['BUS_CAPACITY']
    NUM_BUSES = params['NUM_BUSES']
    BOARDING_TIME = params['BOARDING_TIME']
    PRIORITY_PROB = params['PRIORITY_PROB']
    SIM_TIME = params['SIM_TIME']
    MAX_STOP_TIME = params['MAX_STOP_TIME']
    INITIAL_BUS_DELAY = params['INITIAL_BUS_DELAY']

    # Data collection
    data = []  # Boarded passengers: {'passenger': name, 'priority': priority_name, 'wait_time': wait_time, 'bus_id': bus_id}
    queue_lengths = []  # (time, queue_size)
    bus_occupancies = {i: [] for i in range(NUM_BUSES)}  # Per bus: list of (time, occupancy)
    log_lines = []  # For file output

    # Priority queue for waiting passengers: heapq with (priority, arrival_time, name, priority_name, boarded_event)
    waiting_passengers = []

    def log_message(message):
        #Log message to list and print.
        log_lines.append(f"{env.now:.2f}: {message}")
        print(message)

    def passenger(env, name, priority, priority_name):
        #Process for a single passenger: arrive, enqueue, wait until boarded.
        arrival_time = env.now
        boarded_event = env.event()  # Event to signal when passenger is boarded
        heapq.heappush(waiting_passengers, (priority, arrival_time, name, priority_name, boarded_event))
        # Record queue size at arrival for average queue computation
        queue_lengths.append((env.now, len(waiting_passengers)))
        log_message(f"{name} ({priority_name}) arriving at {env.now:.2f}")
        yield boarded_event  # Wait until a bus process boards this passenger
        wait_time = env.now - arrival_time
        data.append({
            'passenger': name,
            'priority': priority_name,
            'wait_time': wait_time,
            'bus_id': boarded_event.bus_id  # Set by bus process
        })

    def passenger_generator(env):
        #Generate passengers with random priorities.
        i = 0
        while True:
            yield env.timeout(random.expovariate(PASSENGER_ARRIVAL_RATE / 3600))
            is_priority = random.random() < PRIORITY_PROB
            priority = 0 if is_priority else 1  # Lower number = higher priority
            priority_name = 'Priority' if is_priority else 'Normal'
            env.process(passenger(env, f'Passenger_{i}', priority, priority_name))
            i += 1

    def bus(env, bus_id):
        #Bus arrives, boards passengers until full or max stop time, and departs.
        # Stagger initial arrival with additional initial delay
        initial_delay = INITIAL_BUS_DELAY + bus_id * (BUS_INTERVAL / NUM_BUSES)
        yield env.timeout(initial_delay)
        
        while True:
            # Arrive at stop
            log_message(f"Bus {bus_id} arriving at {env.now:.2f}")
            occupancy = 0
            
            # Board passengers until full or max stop time reached
            stop_start = env.now
            boarded = 0
            while (waiting_passengers and occupancy < BUS_CAPACITY) and (env.now - stop_start) < MAX_STOP_TIME:
                if waiting_passengers and occupancy < BUS_CAPACITY:
                    # Pop the highest priority
                    (priority, arrival_time, name, priority_name, boarded_event) = heapq.heappop(waiting_passengers)
                    wait_time = env.now - arrival_time
                    log_message(f"{name} ({priority_name}) boarding Bus {bus_id} at {env.now:.2f} (waited {wait_time:.2f} sec)")
                    yield env.timeout(BOARDING_TIME)
                    occupancy += 1
                    boarded += 1
                    boarded_event.bus_id = bus_id
                    boarded_event.succeed()
                else:
                    # No passengers or full: yield a small time to allow new arrivals
                    yield env.timeout(1)  # Small tick to check again
                    
            queue_lengths.append((env.now, len(waiting_passengers)))
            
            # Record occupancy at departure
            bus_occupancies[bus_id].append((env.now, occupancy))
            # Depart
            log_message(f"Bus {bus_id} departing at {env.now:.2f} with {occupancy} passengers")
            
            # Wait for next arrival (full BUS_INTERVAL from arrival time)
            time_since_arrival = env.now - stop_start
            remaining_interval = BUS_INTERVAL - time_since_arrival
            if remaining_interval > 0:
                yield env.timeout(remaining_interval)
            else:
                yield env.timeout(1)  # Small delay

    # Setup and run simulation
    random.seed(42)
    env = simpy.Environment()
    # Start bus processes (one per bus id)
    for i in range(NUM_BUSES):
        env.process(bus(env, i))
     # Start passenger arrival generator
     
    env.process(passenger_generator(env))
    env.run(until=SIM_TIME)  # Run simulation until SIM_TIME

    # Analyze results
    wait_times = {'Priority': [], 'Normal': []}
    for entry in data:
        wait_times[entry['priority']].append(entry['wait_time'])

    results = {
        'wait_times': {},
        'avg_queue': int(sum(size for _, size in queue_lengths) / len(queue_lengths)) if queue_lengths else 0,
        'avg_occupancy': sum(sum(seats for _, seats in occ) / len(occ) for occ in bus_occupancies.values() if occ) / NUM_BUSES if any(bus_occupancies.values()) else 0,
        'throughput': len(data) * 3600 / SIM_TIME if data else 0
    }
    for priority in wait_times:
        times = wait_times[priority]
        results['wait_times'][priority] = (sum(times) / len(times))/60 if times else 0

    # Write log to file
    with open('simulation_log.txt', 'w') as f:
        f.write('\n'.join(log_lines))

    return results, data, queue_lengths, bus_occupancies

# Get user input and run simulation
params = get_user_input()
results, data, queue_lengths, bus_occupancies = run_simulation(params)

# Print results
print(f"\n=== Results for {params['NUM_BUSES']} Buses, {params['BUS_INTERVAL']}s Interval ===")
for priority in results['wait_times']:
    print(f"Average wait time for {priority}: {results['wait_times'][priority]:.2f} Minutes")
print(f"Average queue length: {results['avg_queue']:.2f} passengers ")
print(f"Average bus occupancy: {results['avg_occupancy']:.2f} seats ({results['avg_occupancy'] / params['BUS_CAPACITY'] * 100:.2f}% utilization)")
print(f"Throughput: {results['throughput']:.2f} passengers/hour")