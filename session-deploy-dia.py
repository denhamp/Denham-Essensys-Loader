import requests
import json
import uuid
import sys
import re
from urllib.parse import urlparse
import yaml
import getpass

config_file = sys.argv[1]

with open(config_file, 'r') as config:
    config_data = yaml.safe_load(config)
print(config_data['tenant'])
tenant_url = config_data['tenant']['url']
username = config_data['tenant']['username']

source_file = config_data['source']['file']

agentName = config_data['agent']['name']
agentLat = config_data['agent']['lat']
agentLon = config_data['agent']['lon']
agentcity = config_data['agent']['city']
sitecode = config_data['agent']['sitecode']
site_name = config_data['agent']['site_name']
agentrole = config_data['agent']['agentrole']

password = getpass.getpass(prompt='Enter your tenant password: ')

# SOURCE FILE FOR SESSION CONFIGURATION DATA: INCLUDES CLOUD, LOCATION AND DESTINATION URL FOR SELECTED AGENT
# source_file = sys.argv[1]
# login_session_tenant = sys.argv[2]
# agentName = sys.argv[3]
# agentLocation = sys.argv[4]
# username = sys.argv[5]
# password = sys.argv[6]

# LOGIN USING SESSION OBJECT WHICH CACHES AUTH TOKEN FOR LATER REQUESTS
login_session = requests.Session()
location_session = requests.Session()
metadata_session = requests.Session()

# TENANT NAME
# ADD PROTOCOL AND URL
login_session_url = tenant_url + "/api/v1/auth/login"
print("login_session_url ", login_session_url)
login_session_headers = {
    'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
login_session_payload = {'username': username, 'password': password}
login_session_post = login_session.post(
    login_session_url, headers=login_session_headers, data=login_session_payload)
token = (login_session_post.headers['Authorization'])
print('login success')

# SESSION CONFIGURATION API INFO
session_config_url = tenant_url + "/api/orchestrate/v3/agents/session"
api_headers = {'Content-Type': 'application/vnd.api+json',
               'Accept': 'application/json', 'Authorization': token}

# AGENT NAME
print(agentName)
# GET AGENT ID FROM API LOOKUP FUNCTION

agent_list_url = tenant_url + "/api/orchestrate/v3/agents"
print(agent_list_url)


# FUNCTION TO ADD SESSIONS FROM FILE CONTENTS TO SKYLIGHT AGENT ORCHESTRATION API
def add_session():
    # GET AGENT ID FROM API LOOKUP FUNCTION
    agent_list_get = login_session.get(agent_list_url, headers=api_headers)
    agent_list_get_text = agent_list_get.text
    print(agent_list_get_text)
    agent_list_get_json = json.loads(agent_list_get_text)
    agent_list_get_data = agent_list_get_json["data"]
    print(agent_list_get_data)
    for agent_record in agent_list_get_data:
        if agent_record["attributes"]["agentName"] == agentName:
            agentId = agent_record["id"]
    print("agentId ", agentId)
    # OBTAIN SESSION PARAMETERS FROM JSON FILE
    session_source_data = open(source_file)
    session_json = json.load(session_source_data)
    print(session_json)

    for items in session_json:
        AppName = items["AppName"]
        app = items['app']
        # location = items["location"]
        # CREATE SESSION NAME AS CONCATENATION OF AGENT NAME & APPLICATION & SUBAPP (WHICH MAY BE BLANK)
        sessionName = agentName + "-" + AppName
        destinationUrl = items["destinationUrl"]
        # CREATE SESSION ID FROM UUID GENERATOR MODULE
        sessionId = str(uuid.uuid4())
        # BRING VALUES INTO JSON FORMAT FOR API
        session_data = {
            "data": {
                "type": "agentSessions",
                "attributes": {
                    "agentId": agentId,
                    "session": {
                        "sessionId": sessionId,
                        "sessionName": sessionName,
                        "sessionType": "transfer",
                        "enable": True,
                        "period": "repeat",
                        "transfer": {
                            "destinationUrl": destinationUrl,
                            "maximumTestConnectSec": 5,
                            "maximumTestDurationSec": 10,
                            "testInterval": 60,
                            "useProxy": False
                        }
                    }
                }
            }
        }
        # POST SESSION DATA TO API AS JSON
        # add_session_post = login_session.post(
        #     session_config_url, headers=api_headers, data=json.dumps(session_data))
        # add_session_post_text = add_session_post.text

        parse_url = urlparse(destinationUrl)
        parse_url = str(parse_url.netloc)
        parse_url = parse_url.split(':', 1)
        location_url = "http://ip-api.com/json/" + str(parse_url[0])
        location_session_post = location_session.get(location_url)
        geo_data = location_session_post.json()
        geo_lat = geo_data['lat']
        geo_lon = geo_data['lon']
        print('SessionName ' + sessionName)
        print('lat ' + str(geo_lat))
        print('lon ' + str(geo_lon))
        print('app ' + app)

        meta_url = tenant_url + \
            "/api/v2/bulk/insert/monitored-objects/meta"

        session_data = {
            "data": {
                "type": "monitoredObjectsMeta",
                "attributes": {
                    "metadata-entries": [
                        {
                            "objectName": sessionName,
                            "metadata": {
                                "app_id": str(app),
                                "destination_url": str(destinationUrl),
                                "source_location": str(sitecode),
                                "site_name": str(site_name),
                                "sitecode": str(sitecode),
                                "agent_role": str(agentrole)
                            },
                            "sourceLocation": {
                                "lat": agentLat,
                                "lon": agentLon
                            },
                            "destinationLocation": {
                                "lat": geo_lat,
                                "lon": geo_lon
                            }
                        }
                    ]
                }
            }
        }

        print('session_data', session_data)
        # POST SESSION DATA TO API AS JSON
        metadata_session_post = metadata_session.post(
            meta_url, headers=api_headers, data=json.dumps(session_data))
        # PRINT RESPONSE
        print('metadata_session_post ', metadata_session_post)
        metadata_session_post_text = metadata_session_post.text
        print('metadata_session_post_text ', metadata_session_post_text)

        session_source_data.close()


add_session()
