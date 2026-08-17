import base64
from datetime import datetime
import json
import random
import requests
import paho.mqtt.client as mqtt

# --- CONFIGURATION ---
AP_IP = "192.168.1.100"
USERNAME = "admin"
PASSWORD = "yourAdminPassword"

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_USER = "mqtt-user"
MQTT_PASS = "mqtt-password"

# Base64 encode the AP password
password_b64 = base64.b64encode(PASSWORD.encode("utf-8")).decode("utf-8")

# Generate the timestamp parameter expected by the Tenda web server
now = datetime.now()
time_param = f"{now.year};{now.month};{now.day};{now.hour};{now.minute};{now.second};"

auth_payload = {
    "username": USERNAME,
    "password": password_b64,
    "timeZone": "12",
    "time": time_param,
}

session = requests.Session()

# --- 1. FETCH DATA FROM TENDA AP4 ---
try:
    # Perform authentication to acquire session cookie
    session.post(f"http://{AP_IP}/login/Auth", data=auth_payload, timeout=5)

    # Generate a random cache-buster float parameter (emulating Math.random())
    rand_t = random.random()
    response = session.get(
        f"http://{AP_IP}/goform/getSysStatusInfo?wrlRadio=2.4G&t={rand_t}",
        timeout=5,
    )
    data = response.json()

    sys_info = data.get("sysStatus", {})
    wrl_info = data.get("wrlStatus", {})

    # Map raw JSON fields to state payload
    state_payload = {
        "status": "online",
        # --- System Status ---
        "run_time": int(sys_info.get("runTime", 0)),
        "dev_name": sys_info.get("devName", ""),
        "firmware": sys_info.get("fireversion", "").strip(),
        "sys_time": sys_info.get("sysTime", ""),
        "cpu": int(sys_info.get("cpu", "0%").replace("%", "")),
        "ram": int(sys_info.get("ram", "0%").replace("%", "")),
        "hw_version": sys_info.get("hwVersion", ""),
        "lan_ip": sys_info.get("lanIp", ""),
        "lan_mac": sys_info.get("lanMac", ""),
        "wrl_mac": sys_info.get("wrlMac", ""),
        "lan_speed": sys_info.get("lanSpeed", ""),
        "dev_mode": sys_info.get("devMode", ""),
        "wan_status": sys_info.get("wanStatus", ""),
        "wan_ip": (
            sys_info.get("wanIp", "N/A")
            if sys_info.get("wanIp")
            else "Disconnected"
        ),
        # --- Wireless Status ---
        "tx_link": wrl_info.get("txLink", ""),
        "remote_ap_mac": wrl_info.get("remoteApMac", ""),
        "channel_band": wrl_info.get("channelBand", ""),
        "wrl_client": int(wrl_info.get("wrlClient", 0)),
        "ssid": wrl_info.get("ssid", ""),
        "sec_type": wrl_info.get("secType", ""),
        "encrypt_type": wrl_info.get("encryptType", ""),
        "tx_speed": wrl_info.get("txSpeed", ""),
        "signal": int(wrl_info.get("signal", 0)),
        "noise": int(wrl_info.get("noise", 0)),
        "tx_power": int(wrl_info.get("txPower", 0)),
        "band_width": wrl_info.get("bandWidth", ""),
        "work_mode": wrl_info.get("workMode", ""),
    }

except Exception as e:
    state_payload = {"status": "offline", "error": str(e)}

# --- 2. MQTT CLIENT SETUP ---
client = mqtt.Client(client_id="tenda_ap4")

if MQTT_USER and MQTT_PASS:
    client.username_pw_set(MQTT_USER, MQTT_PASS)

client.connect(MQTT_BROKER, MQTT_PORT, 60)

# --- 3. HOME ASSISTANT DEVICE METADATA ---
device_info = {
    "identifiers": ["tenda_ap4_cc2d21"],
    "name": "Tenda AP4 Access Point",
    "model": state_payload.get("dev_name", "AP4 V2.0"),
    "manufacturer": "Tenda",
    "sw_version": state_payload.get("firmware", "V1.0.0.4"),
    "hw_version": state_payload.get("hw_version", "V2.0"),
}

# --- 4. HOME ASSISTANT MQTT DISCOVERY CONFIGURATION ---
sensors = [
    # Main Performance & Status Sensors
    {
        "id": "status",
        "name": "Status",
        "icon": "mdi:router-wireless",
        "val": "{{ value_json.status }}",
    },
    {
        "id": "wrl_client",
        "name": "Connected Clients",
        "unit": "clients",
        "icon": "mdi:wifi-check",
        "val": "{{ value_json.wrl_client }}",
    },
    {
        "id": "cpu",
        "name": "CPU Usage",
        "unit": "%",
        "icon": "mdi:cpu-64-bit",
        "val": "{{ value_json.cpu }}",
    },
    {
        "id": "ram",
        "name": "RAM Usage",
        "unit": "%",
        "icon": "mdi:memory",
        "val": "{{ value_json.ram }}",
    },
    {
        "id": "signal",
        "name": "Uplink Signal Strength",
        "unit": "dBm",
        "dev_cls": "signal_strength",
        "val": "{{ value_json.signal }}",
    },
    {
        "id": "noise",
        "name": "Noise Level",
        "unit": "dBm",
        "dev_cls": "signal_strength",
        "val": "{{ value_json.noise }}",
    },
    {
        "id": "tx_speed",
        "name": "Link Speed (TX/RX)",
        "icon": "mdi:speedometer",
        "val": "{{ value_json.tx_speed }}",
    },
    {
        "id": "run_time",
        "name": "Uptime",
        "unit": "s",
        "icon": "mdi:timer-outline",
        "val": "{{ value_json.run_time }}",
    },
    {
        "id": "ssid",
        "name": "Connected SSID",
        "icon": "mdi:wifi",
        "val": "{{ value_json.ssid }}",
    },
    {
        "id": "channel_band",
        "name": "Wi-Fi Channel",
        "icon": "mdi:wifi-cog",
        "val": "{{ value_json.channel_band }}",
    },
    {
        "id": "band_width",
        "name": "Channel Bandwidth",
        "unit": "MHz",
        "icon": "mdi:arrow-expand-horizontal",
        "val": "{{ value_json.band_width }}",
    },
    {
        "id": "tx_power",
        "name": "Transmit Power",
        "unit": "dBm",
        "icon": "mdi:transmission-tower",
        "val": "{{ value_json.tx_power }}",
    },
    # Diagnostic Sensors
    {
        "id": "lan_ip",
        "name": "LAN IP",
        "icon": "mdi:ip-network",
        "val": "{{ value_json.lan_ip }}",
        "cat": "diagnostic",
    },
    {
        "id": "lan_mac",
        "name": "LAN MAC Address",
        "icon": "mdi:network-outline",
        "val": "{{ value_json.lan_mac }}",
        "cat": "diagnostic",
    },
    {
        "id": "wrl_mac",
        "name": "Wi-Fi MAC Address",
        "icon": "mdi:wifi-star",
        "val": "{{ value_json.wrl_mac }}",
        "cat": "diagnostic",
    },
    {
        "id": "remote_ap_mac",
        "name": "Remote AP MAC Address",
        "icon": "mdi:router-wireless-settings",
        "val": "{{ value_json.remote_ap_mac }}",
        "cat": "diagnostic",
    },
    {
        "id": "lan_speed",
        "name": "LAN Port Speed",
        "icon": "mdi:ethernet",
        "val": "{{ value_json.lan_speed }}",
        "cat": "diagnostic",
    },
    {
        "id": "sec_type",
        "name": "Security Type",
        "icon": "mdi:shield-lock",
        "val": "{{ value_json.sec_type }}",
        "cat": "diagnostic",
    },
    {
        "id": "encrypt_type",
        "name": "Encryption Type",
        "icon": "mdi:lock-check",
        "val": "{{ value_json.encrypt_type }}",
        "cat": "diagnostic",
    },
    {
        "id": "work_mode",
        "name": "Operation Mode",
        "icon": "mdi:cog",
        "val": "{{ value_json.work_mode }}",
        "cat": "diagnostic",
    },
    {
        "id": "tx_link",
        "name": "Antenna Configuration",
        "icon": "mdi:antenna",
        "val": "{{ value_json.tx_link }}",
        "cat": "diagnostic",
    },
    {
        "id": "sys_time",
        "name": "System Time",
        "icon": "mdi:clock-outline",
        "val": "{{ value_json.sys_time }}",
        "cat": "diagnostic",
    },
]

# Publish Discovery configs to Home Assistant
for s in sensors:
    config_topic = f"homeassistant/sensor/tenda_ap4/{s['id']}/config"
    config_payload = {
        "name": s["name"],
        "unique_id": f"tenda_ap4_{s['id']}",
        "state_topic": "tenda_ap4/state",
        "value_template": s["val"],
        "device": device_info,
    }
    if "unit" in s:
        config_payload["unit_of_measurement"] = s["unit"]
    if "icon" in s:
        config_payload["icon"] = s["icon"]
    if "dev_cls" in s:
        config_payload["device_class"] = s["dev_cls"]
    if "cat" in s:
        config_payload["entity_category"] = s["cat"]

    client.publish(config_topic, json.dumps(config_payload), retain=True)

# --- 5. PUBLISH STATE DATA ---
client.publish("tenda_ap4/state", json.dumps(state_payload), retain=True)
client.disconnect()