#!/usr/bin/env python3
"""
Enhanced SUMO Injection Script for Unix Timestamps
This script injects vehicles and anomalies from a cleaned dataset with Unix timestamps
into a SUMO simulation and exports detailed logs and timestamped traffic data.
"""

import traci
import pandas as pd
import numpy as np
import time
import random
import os
import sys
import datetime
from pathlib import Path

def setup_logging(output_dir):
    """Set up directories for logging simulation data"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path(output_dir) / f"simulation_{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories for different log types
    (log_dir / "traffic").mkdir(exist_ok=True)
    (log_dir / "anomalies").mkdir(exist_ok=True)
    
    print(f"Logs will be saved to: {log_dir}")
    return log_dir

def log_traffic_data(log_dir, step, vehicles_data):
    """Log detailed traffic data for the current simulation step"""
    if not vehicles_data:
        return
    
    filename = log_dir / "traffic" / f"traffic_step_{step:.1f}.csv"
    df = pd.DataFrame(vehicles_data)
    df.to_csv(filename, index=False)

def log_anomaly_data(log_dir, anomalies_data):
    """Log anomaly data at the end of simulation"""
    if not anomalies_data:
        return
    
    filename = log_dir / "anomalies" / "anomalies.csv"
    df = pd.DataFrame(anomalies_data)
    df.to_csv(filename, index=False)

def run_simulation(input_csv, sumo_config, output_dir, duration=3600, sample_rate=0.01):
    """
    Run the SUMO simulation with data injection and logging
    
    Parameters:
    -----------
    input_csv : str
        Path to the cleaned IoV dataset
    sumo_config : str
        Path to the SUMO configuration file
    output_dir : str
        Directory to save logs
    duration : int
        Simulation duration in seconds
    sample_rate : float
        Rate at which to sample from the dataset (0.01 = 1%)
    """
    log_dir = setup_logging(output_dir)
    
    try:
        # Load dataset
        print(f"Loading dataset from {input_csv}...")
        df = pd.read_csv(input_csv)
        print(f"Dataset loaded with {len(df)} entries")
        
        # Handle Unix timestamps by normalizing to simulation time
        min_timestamp = df['timestamp'].min()
        df['sim_time'] = df['timestamp'] - min_timestamp
        
        # Sample the data if there are too many entries
        if sample_rate < 1.0:
            original_size = len(df)
            df = df.sample(frac=sample_rate, random_state=42)
            print(f"Sampled dataset from {original_size} to {len(df)} entries (rate: {sample_rate})")
        
        # Scale timestamps to fit within simulation duration if needed
        max_sim_time = df['sim_time'].max()
        if max_sim_time > duration:
            scale_factor = duration / max_sim_time
            df['sim_time'] = df['sim_time'] * scale_factor
            print(f"Scaled timestamps by factor {scale_factor:.4f} to fit within {duration}s simulation")
        
        # Start SUMO with TraCI
        sumo_cmd = [
            "sumo",
            "-c", os.path.abspath(sumo_config),
            "--step-length", "0.1",   # 100ms time steps
            "--no-warnings", "true"
        ]
        
        traci.start(sumo_cmd, port=8813)
        print("SUMO started successfully!")
        
        # Prepare data structures for the simulation
        df = df.sort_values('sim_time')  # Ensure data is sorted by simulation time
        
        # Create vehicle type for malicious vehicles if it doesn't exist
        try:
            if "malicious_vehicle" not in traci.vehicletype.getIDList():
                traci.vehicletype.copy("car", "malicious_vehicle")
                traci.vehicletype.setColor("malicious_vehicle", (255, 0, 0, 255))  # Red color
                print("Created malicious vehicle type")
        except:
            print("Warning: Could not create malicious vehicle type, using default")
        
        # Variables to track simulation progress
        injected_vehicles = 0
        injected_anomalies = 0
        processed_idx = 0
        anomalies_data = []
        last_log_time = 0
        log_interval = 10  # Log traffic data every 10 seconds
        
        print(f"Starting simulation for {duration} seconds...")
        
        # Main simulation loop
        while traci.simulation.getTime() < duration:
            current_time = traci.simulation.getTime()
            
            # Find entries to inject at the current time step
            # Get data points with timestamp in current time window
            relevant_rows = df[(df['sim_time'] > current_time - 0.1) & 
                              (df['sim_time'] <= current_time)]
            
            # Inject vehicles
            for _, row in relevant_rows.iterrows():
                vehicle_id = f"veh_{int(current_time)}_{random.randint(1000,9999)}"
                vehicle_type = "malicious_vehicle" if row['is_malicious'] == 1 else "car"
                
                try:
                    # Get one of the available routes randomly
                    routes = traci.route.getIDList()
                    route_id = random.choice(routes) if routes else "route0"
                    
                    # Add the vehicle
                    traci.vehicle.add(
                        vehicle_id,
                        route_id,
                        typeID=vehicle_type,
                        depart="now",
                        departSpeed="random"
                    )
                    
                    # Set vehicle color based on malicious status
                    if row['is_malicious'] == 1:
                        traci.vehicle.setColor(vehicle_id, (255, 0, 0, 255))  # Red for malicious
                        injected_anomalies += 1
                        
                        # Collect anomaly data
                        anomaly_data = {
                            'sim_time': current_time,
                            'vehicle_id': vehicle_id,
                            'can_id': row['can_id'],
                            'payload': row['payload'],
                            'attack_category': row['attack_category'],
                            'attack_type': row['attack_type']
                        }
                        anomalies_data.append(anomaly_data)
                        print(f"🚨 Injected malicious vehicle {vehicle_id} at {current_time:.1f}s - {row['attack_type']}")
                    else:
                        traci.vehicle.setColor(vehicle_id, (0, 255, 0, 255))  # Green for normal
                        print(f"🚗 Injected normal vehicle {vehicle_id} at {current_time:.1f}s")
                    
                    injected_vehicles += 1
                    
                except traci.exceptions.TraCIException as e:
                    print(f"Failed to inject vehicle: {e}")
            
            # Collect and log traffic data at regular intervals
            if current_time - last_log_time >= log_interval or current_time < 1:
                vehicles_data = []
                vehicle_ids = traci.vehicle.getIDList()
                
                for veh_id in vehicle_ids:
                    try:
                        position = traci.vehicle.getPosition(veh_id)
                        speed = traci.vehicle.getSpeed(veh_id)
                        accel = traci.vehicle.getAcceleration(veh_id)
                        type_id = traci.vehicle.getTypeID(veh_id)
                        
                        # Collect vehicle data
                        vehicle_data = {
                            "sim_time": current_time,
                            "vehicle_id": veh_id,
                            "x": position[0],
                            "y": position[1],
                            "speed": speed,
                            "acceleration": accel,
                            "is_malicious": 1 if type_id == "malicious_vehicle" else 0
                        }
                        
                        vehicles_data.append(vehicle_data)
                    except traci.exceptions.TraCIException as e:
                        print(f"Error collecting data for vehicle {veh_id}: {e}")
                
                # Log traffic data
                if vehicles_data:
                    log_traffic_data(log_dir, current_time, vehicles_data)
                    print(f"📊 Logged traffic data at {current_time:.1f}s for {len(vehicles_data)} vehicles")
                
                last_log_time = current_time
            
            # Advance simulation
            traci.simulationStep()
            
            # Small delay to reduce CPU load
            time.sleep(0.01)
            
            # Progress indicator (every 100 seconds)
            if int(current_time) % 100 == 0 and current_time > 0 and abs(current_time % 100) < 0.11:
                print(f"Simulation progress: {current_time:.1f}/{duration} seconds ({(current_time/duration*100):.1f}%)")
                print(f"  Vehicles injected so far: {injected_vehicles} ({injected_anomalies} malicious)")
        
        # Log all anomalies
        log_anomaly_data(log_dir, anomalies_data)
        
        # Create a summary file
        summary = {
            'total_vehicles': injected_vehicles,
            'malicious_vehicles': injected_anomalies,
            'simulation_duration': duration,
            'dataset_entries': len(df),
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(log_dir / "simulation_summary.json", 'w') as f:
            import json
            json.dump(summary, f, indent=2)
        
        print("\n--- SIMULATION COMPLETE ---")
        print(f"Total vehicles injected: {injected_vehicles}")
        print(f"Malicious vehicles injected: {injected_anomalies}")
        print(f"All logs saved to: {log_dir}")
        
    except Exception as e:
        print(f"Simulation error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'traci' in locals() and traci.isLoaded():
            traci.close()
        print("Simulation ended")
        return log_dir

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run SUMO simulation with vehicle and anomaly injection')
    parser.add_argument('--input', default='data/cleaned_iov.csv', 
                        help='Path to cleaned dataset CSV')
    parser.add_argument('--config', default='sumo/simple.sumocfg',
                        help='Path to SUMO configuration file')
    parser.add_argument('--output', default='logs',
                        help='Directory to store output logs')
    parser.add_argument('--duration', type=int, default=3600,
                        help='Simulation duration in seconds')
    parser.add_argument('--sample-rate', type=float, default=0.01,
                        help='Sample rate from dataset (0.01 = 1%)')
    
    args = parser.parse_args()
    
    run_simulation(args.input, args.config, args.output, args.duration, args.sample_rate)