
import requests
import random
import time

# Define the endpoint
url = "http://127.0.0.1:8000/sensor/add"

# Define sensor configurations
sensors = [
    {"sensor_id": "temp_sensor_1", "sensor_type": "temperature"},
    {"sensor_id": "humidity_sensor_1", "sensor_type": "humidity"},
    {"sensor_id": "temp_sensor_2", "sensor_type": "temperature"},
]

# Function to generate random sensor data
def generate_sensor_data(sensor_type):
    if sensor_type == "temperature":
        return {"temperature": random.uniform(15, 30), "humidity": random.uniform(40, 60)}
    elif sensor_type == "humidity":
        return {"temperature": random.uniform(20, 25), "humidity": random.uniform(50, 80)}
    return {}

# Number of data points to generate
num_data_points = 100

print(f"Generating {num_data_points} data points for {len(sensors)} sensors...")

for i in range(num_data_points):
    for sensor in sensors:
        data = {
            "sensor_id": sensor["sensor_id"],
            "sensor_type": sensor["sensor_type"],
            **generate_sensor_data(sensor["sensor_type"]),
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"Successfully added data for {sensor['sensor_id']}: {data}")
            else:
                print(f"Failed to add data for {sensor['sensor_id']}. Status: {response.status_code}, Detail: {response.json().get('detail')}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to the server: {e}")
            # Wait and retry if the server is not ready
            time.sleep(5)
    
    # Wait for a short interval between sending data points
    time.sleep(1)

print("Data generation complete!")
