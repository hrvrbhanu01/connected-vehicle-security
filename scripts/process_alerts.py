import json
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class EveJsonHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('eve.json'):
            self.process_alerts(event.src_path)

    def process_alerts(self, file_path):
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    alert = json.loads(line)
                    if alert['event_type'] == 'alert':
                        event_data = {
                            'timestamp': alert['timestamp'],
                            'alert_id': alert['alert']['signature_id'],
                            'attack_type': alert['alert']['signature'],
                            'source_ip': alert['src_ip'],
                            'dest_ip': alert['dest_ip'],
                            'raw_data': alert
                        }
                        self.send_to_blockchain(event_data)
                except json.JSONDecodeError:
                    continue

    def send_to_blockchain(self, event_data):
        try:
            response = requests.post(
                "http://localhost:4000/api/recordEvent",
                json=event_data,
                headers={'Content-Type': 'application/json'}
            )
            print(f"Alert sent to blockchain: {response.status_code}")
        except Exception as e:
            print(f"Error sending to blockchain: {str(e)}")

if __name__ == "__main__":
    path = '/var/log/suricata/'
    event_handler = EveJsonHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()