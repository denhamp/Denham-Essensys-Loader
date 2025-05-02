import json
import uuid
import sys
import re
import yaml
import getpass
from urllib.parse import urlparse

import requests

# Load configuration data from a YAML file
config_file = sys.argv[1]
with open(config_file, 'r') as config:
    config_data = yaml.safe_load(config)

# Extract required values from the configuration
tenant_url = config_data['tenant']['url']
username = config_data['tenant']['username']
password = getpass.getpass(prompt='Enter your tenant password: ')

# Set up sessions for making API requests
login_session = requests.Session()
location_session = requests.Session()

# Authenticate the user and obtain an access token
login_session_url = f"{tenant_url}/api/v1/auth/login"
login_session_headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json'
}
login_session_payload = {'username': username, 'password': password}
response = login_session.post(
    login_session_url,
    headers=login_session_headers,
    data=login_session_payload
)
response.raise_for_status()
token = response.headers['Authorization']

# Set up API request headers that include the access token
api_headers = {
    'Content-Type': 'application/vnd.api+json',
    'Accept': 'application/json',
    'Authorization': token
}

# Extract required values from the configuration
agent_name = config_data['agent']['name']
agent_location = config_data['agent']['location']
agent_lat = config_data['agent']['lat']
agent_lon = config_data['agent']['lon']
source_file = config_data['source']['file']

# Set up API URLs
agent_list_url = f"{tenant_url}/api/orchestrate/v3/agents"
session_config_url = f"{tenant_url}/api/orchestrate/v3/agents/session"
meta_url = f"{tenant_url}/api/v2/bulk/insert/monitored-objects/meta"

# Retrieve the list of agents and find the ID of the agent with the given name
response = login_session.get(agent_list_url, headers=api_headers)
response.raise_for_status()
agent_list_data = response.json()["data"]
agent_id = next(
    (agent_record["id"] for agent_record in agent_list_data if agent_record["attributes"]["agentName"] == agent_name),
    None
)
if not agent_id:
    print(f"Could not find agent with name {agent_name}.")
    sys.exit(1)

# Load session configuration data from a JSON file
with open(source_file) as f:
    session_config_data = json.load(f)

# Create a session for each item in the session configuration data
for session_data in session_config_data:
    app_name = session_data["AppName"]
    app = session_data["app"]
    destination_url = session_data["destinationUrl"]
    session_name = f"{agent_name}-{app_name}"
    session_id = str(uuid.uuid4())

    # Create the request payload for creating the session
    payload = {
        "data": {
            "type": "agentSessions",
            "attributes": {
                "agentId": agent_id,
                "session": {
                    "sessionId": session_id,
                    "sessionName": session_name,
                    "sessionType": "transfer",
                    "enable": True,
                    "period": "repeat",
                    "transfer": {
                        "destinationUrl": destination_url,
                        "maximumTestConnectSec": 5,
                        "maximumTestDurationSec": 10,
                        "testInterval": 60,
                        "useProxy": False
                    }
                }
            }
        }
   
def add_session():
    # PARSE DESTINATION URL TO GET GEOLOCATION
    destination_url = input("Enter destination URL: ")
    parsed_url = urlparse(destination_url)
    domain = parsed_url.netloc.split(':')[0]
    location_url = f"http://ip-api.com/json/{domain}"
    response = requests.get(location_url)
    response.raise_for_status()
    geo_data = response.json()
    geo_lat = geo_data['lat']
    geo_lon = geo_data['lon']

    # GET SESSION SOURCE DATA
    with open('session_source_data.txt', 'r') as session_source_data:
        session_data = session_source_data.read()
        session_name = input("Enter session name: ")
        app = input("Enter app name: ")
        agent_location = input("Enter agent location: ")
        agent_lat = input("Enter agent latitude: ")
        agent_lon = input("Enter agent longitude: ")
        metadata_entry = {
            "objectName": session_name,
            "metadata": {
                "app": app,
                "data_centre": agent_location
            },
            "sourceLocation": {
                "lat": agent_lat,
                "lon": agent_lon
            },
            "destinationLocation": {
                "lat": geo_lat,
                "lon": geo_lon
            }
        }
        session_metadata = {
            "data": {
                "type": "monitoredObjectsMeta",
                "attributes": {
                    "metadata-entries": [metadata_entry]
                }
            }
        }

        # POST SESSION METADATA TO API AS JSON
        meta_url = f"{tenant_url}/api/v2/bulk/insert/monitored-objects/meta"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.post(meta_url, headers=headers, json=session_metadata)
        response.raise_for_status()
        print(response.text)

    session_source_data.close()

add_session()
