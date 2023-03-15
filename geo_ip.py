import requests
import json
import sys
from urllib.parse import urlparse

source_file = sys.argv[1]

login_session = requests.Session()

#Example URL
#https://ip-geolocation.whoisxmlapi.com/api/v1?apiKey=at_bcUyxdkCgwfbNqiZwPxxxLnltCLyX&domain=denham2.hopto.org

login_session_url = "http://ip-api.com/json/"
login_session_headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}

#Open the Data File
session_source_data = open(source_file)
session_json = json.load(session_source_data)
#print(session_json)

for items in session_json:
        # location = items["location"]
        #CREATE SESSION NAME AS CONCATENATION OF AGENT NAME & APPLICATION & SUBAPP (WHICH MAY BE BLANK)
    destinationUrl = items["destinationUrl"]
    print('Destination URL :', destinationUrl)
    parse_url = urlparse(destinationUrl)
    print(parse_url)
    print('Hostname is : ', parse_url.netloc)
        #CREATE SESSION ID FROM UUID GENERATOR MODULE

    login_session_post = login_session.get(login_session_url+str(parse_url.hostname), headers=login_session_headers)
   # print(login_session_post.json())

    geo_data = login_session_post.json()
    print('geo_data is', geo_data)

    geo_lat = geo_data["lat"]
    geo_lng = geo_data["lon"]
    print(geo_lat,geo_lng)
    