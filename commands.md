## running inject_sumo.py script
python3 inject_sumo.py
OR
python3 scripts/inject_sumo.py --input data/cleaned_iov.csv --config sumo/simple.sumocfg --output logs --duration 3600 --sample-rate 0.01


## running suricata :

# Here's how you can install Suricata on Ubuntu/Debian:
sudo apt update
sudo apt install suricata

1. Install suricata rules:
sudo suricata-update

2. Use a proper network interface:
The loopback interface (lo) isn't suitable for most Suricata monitoring. You should use your actual network interface. First, find your active network interfaces:

ip a

3. I see your network interfaces now. Your active wireless interface is wlp0s20f3 with IP address 192.168.1.9.
Let's try running Suricata on your wireless interface:

4. Make sure your custom rules are in place:
sudo mkdir -p /etc/suricata/rules/auto
sudo nano /etc/suricata/rules/auto/connected-vehicle.rules

Add these rules:
# Message Injection Detection
alert ip any any -> any any (msg:"Possible CAN message injection detected"; content:"|27 10|"; depth:4; sid:1000001; rev:1;)

# Sybil Attack Detection
alert ip any any -> any any (msg:"Possible Sybil attack - multiple identities"; threshold:type threshold, track by_src, count 5, seconds 2; sid:1000002; rev:1;)

# Firmware Tampering Detection
alert tcp any any -> any any (msg:"Possible firmware tampering attempt"; content:"FLASH"; nocase; content:"WRITE"; distance:0; nocase; sid:1000003; rev:1;)

5. Update the main Suricata configuration to include your rules:
sudo nano /etc/suricata/suricata.yaml

Find the rule-files section and add your custom rules file:
rule-files:
  - rules/auto/connected-vehicle.rules

Make sure eve-log is properly configured in the outputs section:
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert

6. Run Suricata on the wireless interface
sudo suricata -i wlp0s20f3 -c /etc/suricata/suricata.yaml -l /var/log/suricata/

7. Check for alerts
Once Suricata is running, you can monitor the alerts in real-time:

tail -f /var/log/suricata/eve.json | grep -A 10 '"event_type":"alert"'

Or with jq if installed:
tail -f /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'




## to run the blockchain network and deploying chaincode as well, just run :
chmod +x network.sh

./network.sh up  OR  ./network.sh down --> to bring the network down!

....delete the wallet folder created in the api-server/
## then run:
node enrollAdmin.js
node registerUser.js

node server.js   ---->  to run the blockchain-api server.