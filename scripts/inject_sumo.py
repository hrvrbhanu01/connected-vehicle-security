import traci
import pandas as pd
import time
import random

def run_simulation():
    sumo_cmd = ["sumo-gui", "-c", "sumo/simple.sumocfg"]
    traci.start(sumo_cmd)
    
    # Load attack data
    df = pd.read_csv('data/cleaned_iov.csv')
    
    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # Inject attacks based on dataset
        for _, row in df[df['timestamp'] <= step].iterrows():
            if row['attack_type'] != 'normal':
                vehicle_id = f"veh_{step}_{random.randint(1000,9999)}"
                traci.vehicle.add(
                    vehicle_id, 
                    "route0",
                    typeID="car",
                    depart=step,
                    departSpeed="random"
                )
                print(f"Injected {row['attack_type']} at step {step}")
        
        step += 1
        time.sleep(0.1)
    
    traci.close()

if __name__ == "__main__":
    run_simulation()