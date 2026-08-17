# Tenda AP4 Access Point to Home Assistant via MQTT

Lightweight Python script to bridge **Tenda AP4 Access Points (V2.0)** with **Home Assistant** using **MQTT Discovery**. 

Instead of relying on fragile web scraping, this script queries the native internal GoAhead API endpoint (`/goform/getSysStatusInfo`) used by the Tenda web interface. It automatically maps and publishes over 20 telemetry metrics directly into Home Assistant under a single, unified device card.

---

## Features

- **Automated HA MQTT Discovery**: Automatically creates and configures all entities in Home Assistant without manual YAML setup.
- **20+ Telemetry Sensors**:
  - **Performance & Status**: Status, Connected Clients, CPU Usage, RAM Usage, Link Speed, Uplink Signal Strength, Noise Level, Transmit Power, Wi-Fi Channel, Bandwidth, and Uptime.
  - **Diagnostics**: LAN IP, LAN MAC, Wi-Fi MAC, Remote AP MAC, LAN Speed, Security Type, Encryption, Operation Mode, Antenna Configuration, and System Time.
- **Zero Extra Dependencies**: Uses clean standard Python and lightweight `paho-mqtt` / `requests` libraries.
- **Native HA Categorization**: Separates performance metrics from diagnostic info into proper Home Assistant entity categories.

---

## Prerequisites

1. **Python 3.8+** installed on your host system or Home Assistant instance.
2. A running **MQTT Broker** (e.g., Mosquitto MQTT Add-on in Home Assistant).
3. `paho-mqtt` and `requests` Python packages installed:
   &grave;&grave;&grave;bash
   pip install paho-mqtt requests
   &grave;&grave;&grave;

---

## Installation & Setup

### 1. Download Script
Clone this repository or download `tenda_ap4.py` to your Home Assistant machine (e.g., under `/config/scripts/`):

```bash
mkdir -p /config/scripts
cd /config/scripts
wget https://raw.githubusercontent.com/YOUR_USERNAME/tenda-ap4-mqtt-ha/main/tenda_ap4.py
```

### 2. Configure Credentials
Open `tenda_ap4.py` and update the configuration parameters at the top of the file:

```python
# --- CONFIGURATION ---
AP_IP = "192.168.1.100"        # Your Tenda AP4 IP Address
USERNAME = "admin"            # Access Point Admin Username
PASSWORD = "yourAdminPassword"# Access Point Admin Password

MQTT_BROKER = "127.0.0.1"     # MQTT Broker IP Address
MQTT_PORT = 1883              # MQTT Port
MQTT_USER = "mqtt-user"       # MQTT Username (leave empty if none)
MQTT_PASS = "mqtt-password"   # MQTT Password (leave empty if none)
```

### 3. Test Execution
Run the script manually from your terminal to verify connection and MQTT discovery:

```bash
python3 /config/scripts/tenda_ap4.py
```

Check your Home Assistant instance under **Settings > Devices & Services > Devices**. You should see a new device named **Tenda AP4 Access Point**.

---

## Home Assistant Automation Setup

To keep telemetry updated automatically, configure Home Assistant to execute the script periodically (e.g., every 2 minutes).

### Step 1: Register Shell Command
Add the following block to your Home Assistant `configuration.yaml`:

```yaml
shell_command:
  tenda_ap4_updater: "python3 /config/scripts/tenda_ap4.py"
```

*Reload Shell Commands via **Developer Tools > YAML > Shell Command** or restart Home Assistant.*

### Step 2: Create Automation
Add this automation via the HA UI (**Settings > Automations & Scenes > Create Automation > Edit as YAML**) or directly in `automations.yaml`:

```yaml
alias: "Tenda AP4: Update MQTT Data"
description: "Triggers the Python polling script every 2 minutes to update Tenda AP4 telemetry via MQTT."
trigger:
  - platform: time_pattern
    minutes: "/2"
condition: []
action:
  - action: shell_command.tenda_ap4_updater
mode: single
```

---

## Dashboard Preview

Once configured, Home Assistant will automatically display all entities grouped cleanly under the device view:

- **Sensors**: CPU %, RAM %, Connected Clients, Signal dBm, Channel, Uptime.
- **Diagnostic Panel**: MAC Addresses, Firmware Version, Hardware Revision, Security Setup.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
