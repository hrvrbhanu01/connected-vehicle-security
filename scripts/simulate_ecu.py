import time
import random
import requests

class ECUSimulator:
    def __init__(self, ecu_id):
        self.ecu_id = ecu_id
        self.normal_messages = [
            {"type": "speed", "value": 60},
            {"type": "rpm", "value": 2000},
            {"type": "temp", "value": 85}
        ]
        self.attack_messages = [
            {"type": "malicious", "value": "inject"},
            {"type": "spoof", "value": "fake_id"},
            {"type": "flood", "value": "1000msgs"}
        ]

    def run(self, attack_probability=0.2):
        while True:
            if random.random() < attack_probability:
                message = random.choice(self.attack_messages)
                print(f"ECU {self.ecu_id} sending attack: {message}")
            else:
                message = random.choice(self.normal_messages)
                print(f"ECU {self.ecu_id} sending normal: {message}")

            try:
                requests.post(
                    "http://localhost:4000/api/recordEvent",
                    json={
                        "timestamp": int(time.time()),
                        "ecu_id": self.ecu_id,
                        "message": message
                    }
                )
            except Exception as e:
                print(f"Error sending message: {str(e)}")

            time.sleep(random.uniform(0.5, 2.0))

if __name__ == "__main__":
    ecu = ECUSimulator("ECU_2")
    ecu.run()