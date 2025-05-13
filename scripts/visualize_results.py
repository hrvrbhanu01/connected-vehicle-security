import pandas as pd
import matplotlib.pyplot as plt

def visualize_detection_rates():
    # Load data from Suricata logs
    with open('suricata/eve.json') as f:
        alerts = [json.loads(line) for line in f if 'alert' in line]
    
    df = pd.DataFrame(alerts)
    attack_counts = df['alert']['signature'].value_counts()
    
    plt.figure(figsize=(10, 6))
    attack_counts.plot(kind='bar')
    plt.title('Attack Detection Counts by Type')
    plt.ylabel('Count')
    plt.xlabel('Attack Type')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('results/detection_counts.png')
    plt.close()

if __name__ == "__main__":
    visualize_detection_rates()