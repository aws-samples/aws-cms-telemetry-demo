# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

#!/usr/bin/env python3

import argparse
import logging
import json
import sys
import requests
import uuid
import time
import csv
import boto3
import botocore 
from utils.config_loader import Config
from pprint import pprint as pretty
import json
import random
from pathlib import Path

from collections import namedtuple

import datetime

from payloadHandler import payloadHandler 

from cmsHandler import ConnectedMobility
from cognitoHandler import Cognito
from iotHandler import IOT
from awsiot import mqtt_connection_builder
from awscrt import io, mqtt, auth, http

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def on_connection_interrupted(self, connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))

# Callback when an interrupted connection is re-established.
def on_connection_resumed(self, connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(self.on_resubscribe_complete)

def main(profile, vin):

   maxspeed = 0
   totalspeed = 0
   avg_speed = 0
   counter = 0
   #Set Config path
   CONFIG_PATH = 'config.ini'
   payloadhandler = payloadHandler(CONFIG_PATH)
   config = Config(CONFIG_PATH)
   config_parameters = config.get_section('SETTINGS')
   i = IOT(profile,"", "", CONFIG_PATH)   
   ENDPOINT = i.iotEndpoint
   
   CLIENT_ID = vin
   PATH_TO_CERT = "{}/{}".format(config_parameters['SECURE_CERT_PATH'].format(unique_id=CLIENT_ID), config_parameters['PROD_CERT'])
   PATH_TO_KEY = "{}/{}".format(config_parameters['SECURE_CERT_PATH'].format(unique_id=CLIENT_ID), config_parameters['PROD_KEY'])
   PATH_TO_ROOT = "{}/{}".format(config_parameters['ROOT_CERT_PATH'], config_parameters['ROOT_CERT'])

   event_loop_group = io.EventLoopGroup(1)
   host_resolver = io.DefaultHostResolver(event_loop_group)
   client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

   test_MQTTClient = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=PATH_TO_CERT,
        pri_key_filepath=PATH_TO_KEY,
        client_bootstrap=client_bootstrap,
        ca_filepath=PATH_TO_ROOT,
        client_id=CLIENT_ID,
        clean_session=False,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        keep_alive_secs=6)
   
   print("Connecting with Prod certs to {} with client ID '{}'...".format(ENDPOINT, CLIENT_ID))
   connect_future = test_MQTTClient.connect()
 
   connect_future.result()
   print("Connected with production certificates to the endpoint")
        
   #setup trip payload
   tripId = uuid.uuid4().hex
   print("Generating Trip ID of {}".format(tripId))
   latLongDict = payloadhandler.generateLatLongFromMiscCSV()
   print("Begin publishing trip data.  Will publish {} payloads".format(len(latLongDict)))
   startCoords = next(iter(latLongDict))
   endCoords = list(latLongDict)[-1]
   startTime = payloadhandler.getTimestampMS()

   for i in latLongDict:
       if i.speed_mph > maxspeed:
            maxspeed = i.speed_mph
       logger.info("Calculate Avg Speed")
       totalspeed = totalspeed + i.speed_mph
       avg_speed = (totalspeed / (counter + 1))
       ts = str(datetime.datetime.now().isoformat())
       if counter == 0:
            logger.info("Setup start of trip payload")
            start_location_lat = i.x_pos/1000
            start_location_long = i.y_pos/1000
            start_time = ts

       payload = payloadhandler.getMiscPayload(i, vin, ts, maxspeed, avg_speed, tripId)
       time.sleep(1)
       print(payload)
       payloadhandler.publishMiscPayload(test_MQTTClient, payload, CLIENT_ID)
       logger.info("Successfully published misc coordinates {} of {}".format(counter, len(latLongDict)))
       counter=counter+1
    
   trippayload = payloadhandler.getTripPayload2(ts, start_location_lat, start_location_long, i.x_pos/1000, i.y_pos/1000, maxspeed, avg_speed, tripId, CLIENT_ID)
   print(trippayload)

   payloadhandler.publishTripPayload(test_MQTTClient, trippayload, CLIENT_ID) 
   
   print("Trip data published sucessfully")   
   exit()
           
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser('generateTelemetry.py')

    parser.add_argument("-p", "--profile", action="store", dest="profile", default=None, help="AWS CLI profile")
    parser.add_argument("-v", "--VIN", action="store", dest="vin", default=None, help="VIN for vehicle")
    
    args = parser.parse_args()

    if args.profile and args.vin:
        main(args.profile, args.vin)
    else:
        print('[Error] Missing Arguments..')
        parser.print_help()

