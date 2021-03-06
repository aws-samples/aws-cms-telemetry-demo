import requests
import json
import csv
import logging
from awscrt import mqtt
from datetime import datetime
from collections import namedtuple
from utils.config_loader import Config

#TODO://a lot
class payloadHandler():
    def __init__(self, file_path):
        super().__init__()
        
        logging.basicConfig(level=logging.ERROR)
        self.logger = logging.getLogger(__name__)
        
        #Load configuration settings from config.ini
        config = Config(file_path)
        self.config_parameters = config.get_section('SETTINGS')
        self.topic_name = self.config_parameters['TOPIC_NAME']
        self.trips_topic_name = self.config_parameters['TRIP_TOPIC_NAME']
        self.dtc_topic_name = self.config_parameters['DTC_TOPIC_NAME']
        self.misc_topic_name = self.config_parameters['MISC_TOPIC_NAME']
        self.csv_location = self.config_parameters['CSV_LOCATION']
        self.misc_csv_location = self.config_parameters['MISC_CSV_LOCATION']
        self.payload_location = self.config_parameters['PAYLOAD_LOCATION']
        
        self.payload_misc_location = self.config_parameters['MISC_PAYLOAD_LOCATION']
        self.trips_payload_location = self.config_parameters['TRIP_PAYLOAD_LOCATION']
        self.dtc_payload_location = self.config_parameters['DTC_PAYLOAD_LOCATION']
        
    def get_value(self, data,lookup):  # Or whatever definition you like
        res = data
        for item in lookup:
            res = res[item]
        return res

    def replace_value(self,data, lookup, value):
        obj = self.get_value(data, lookup[:-1])
        obj[lookup[-1]] = value
        
    def nested_replace(self, structure, original, new ):
        if type(structure) == list:
            return [self.nested_replace( item, original, new) for item in structure]

        if type(structure) == dict:
            return {key : self.nested_replace(value, original, new)
                for key, value in structure.items() }
        
        if structure == original:
            return new
        else:
            return structure
    
    def publishPayload(self, mqttclient, payload, vin):
        vehicle_topic = self.topic_name.format(deviceid=vin)
        mqttclient.publish(
            topic=vehicle_topic,
            payload=payload,
            qos=mqtt.QoS.AT_LEAST_ONCE)

    def publishTripPayload(self, mqttclient, payload, vin):
        trip_topic = self.trips_topic_name.format(deviceid=vin)
        mqttclient.publish(
            topic=trip_topic,
            payload=payload,
            qos=mqtt.QoS.AT_LEAST_ONCE)

    def publishDTCPayload(self, mqttclient, payload, vin):
        dtc_topic = self.dtc_topic_name.format(deviceid=vin)
        mqttclient.publish(
            topic=dtc_topic,
            payload=payload,
            qos=mqtt.QoS.AT_LEAST_ONCE)

    def publishMiscPayload(self, mqttclient, payload, vin):
        vehicle_topic = self.misc_topic_name.format(deviceid=vin)
        mqttclient.publish(
            topic=vehicle_topic,
            payload=payload,
            qos=mqtt.QoS.AT_LEAST_ONCE)

    def getPayload(self, coords, tripId, vin):
        with open(self.payload_location) as f:
            template = json.load(f)
        
        ts = str(self.getTimestampMS())
        template["MessageId"] = vin + '-' + ts
        template["SimulationId"] = tripId
        template["TripId"] = tripId
        template["CreationTimeStamp"] = ts
        template["SendTimeStamp"] = ts
        template["GeoLocation"]["Latitude"] = coords.x
        template["GeoLocation"]["Longitude"] = coords.y
        template["VIN"] = vin

        return json.dumps(template)
    
    def getMiscPayload(self, i, vin, ts, avg_speed, maxspeed, tripId):
        with open(self.payload_misc_location) as f:
            template = json.load(f)
        
        ##ts = str(self.getTimestampMS())
        template["messageId"] = vin + '-' + ts
        template["simulationid"] = tripId
        template["tripId"] = tripId
        template["creationtimestamp"] = ts
        template["sendtimestamp"] = ts
        template["geolocation"]["latitude"] = i.x_pos/1000
        template["geolocation"]["longitude"] = i.y_pos/1000
        template["geolocation"]["location"] = [ i.y_pos/1000, i.x_pos/1000]
        template["geolocation"]["speed"] = i.speed_mph
        template["speed"]["average"] = avg_speed
        template["speed"]["max"] = maxspeed
        template["vin"] = vin
        template["odometer"]["metres"] = i.odometer
        template["batterycrankingvoltage"] = i.batt_current
        template["devicevoltage"] = i.remaining
        template["stateofcharge"] = i.batt_soc
        template["ignition"] = 1
        template["tires"]["pressure_front_left"] = i.tires_fl
        template["tires"]["pressure_front_right"] = i.tires_fr
        template["tires"]["pressure_rear_left"] = i.tires_rl
        template["tires"]["pressure_rear_right"] = i.tires_rr

        return json.dumps(template)
        
    def getTripPayload(self, startTime, startCoords, endCoords, tripId, vin):
        with open(self.trips_payload_location) as f:
            template = json.load(f)
        
        template["creationtimestamp"] = startTime        
        template["vin"] = vin
        template["tripid"] = tripId
        template["sendtimestamp"] = startTime
        
        template["tripsummary"]["endlocation"]["latitude"] = endCoords.x
        template["tripsummary"]["endlocation"]["longitude"] = endCoords.y

        template["tripsummary"]["startlocation"]["latitude"] = startCoords.x
        template["tripsummary"]["startlocation"]["longitude"] = startCoords.y

        template["tripsummary"]["starttime"] = startTime
        return json.dumps(template)
    
    def getTripPayload2(self, startTime, startCoords_lat, startCoords_long, endCoords_lat, endCoords_long, avg_speed, max_speed, tripId, vin):
        with open(self.trips_payload_location) as f:
            template = json.load(f)
        
        ts = str(self.getTimestampMS())
        template["creationtimestamp"] = ts        
        template["vin"] = vin
        template["tripid"] = tripId
        template["sendtimestamp"] = ts
        
        template["tripsummary"]["endlocation"]["latitude"] = endCoords_lat
        template["tripsummary"]["endlocation"]["longitude"] = endCoords_long

        template["tripsummary"]["startlocation"]["latitude"] = startCoords_lat
        template["tripsummary"]["startlocation"]["longitude"] = startCoords_long

        template["tripsummary"]["starttime"] = startTime
        return json.dumps(template)

    def getDTCPayload(self, dtc, vin):
        with open(self.dtc_payload_location) as f:
            template = json.load(f)
        
        ts = str(self.getTimestampMS())
        template["messageid"] = vin + '-' + ts
        template["creationtimestamp"] = ts
        template["sendtimestamp"] = ts
        template["vin"] = vin
        template["dtc"]["code"] = dtc
        
        return json.dumps(template)
    
    def getTimestampMS(self):
        return datetime.now().astimezone().isoformat()    

    def createRegionObject(self, city, state) -> None:
        i=0
        region = {
            "latitudeMin":39.625923,
            "longitudeMin":-105.036412,
            "latitudeMax":39.833554,
            "longitudeMax":-104.731846
        }
            
        #get regional/city bbox coordinates from OSM
        r = requests.get('https://nominatim.openstreetmap.org/search?q=' + city + ' ' + state + '&format=geojson')
        data = json.loads(r.text)
        
        if data:
            #just take first one, no sense in getting precise
            lst = data['features'][0]['bbox']

            for key in region: 
                region[key]= lst[i]
                i=i+1

        return region

    def createPlaceObject(self,city, state) -> None:
        place = {
            "latitude":0,
            "longitude":0,
        }
        
        #get regional/city bbox coordinates from OSM
        r = requests.get('https://nominatim.openstreetmap.org/search?q=' + city + ' ' + state + '&format=json')
        data = json.loads(r.text)
        if data:
            #just take first one, no sense in getting precise
            place["latitude"] = data[0]["lat"]
            place["longitude"] = data[0]["lon"]

        return place

    #TODO:// make this dynamic CSV
    def generateInitialCoordinatesFromCSV(self):
        coords = namedtuple("Coords", ['x', 'y'])
        a_list = []
        with open('assets/latLong2.csv') as csvfile:
            reader = csv.reader(csvfile,delimiter=",")
            for row in reader:
                a_list.append(coords(float(row[1]), float(row[0])))
                return a_list    
        
    
    def generateLatLongFromCSV(self):
        coords = namedtuple("Coords", ['x', 'y'])
        a_list = []
        with open(self.csv_location) as csvfile:
            reader = csv.reader(csvfile,delimiter=",")
            for row in reader:
                a_list.append(coords(float(row[1]), float(row[0])))
                    
        return a_list

    def generateLatLongFromMiscCSV(self):
        telemetry = namedtuple("telemetry", ['time', 'torque','motor_torque','accel','decel','speed_mph','batt_soc','batt_current','x_pos','y_pos','odometer', 'remaining', 'tires_fl', 'tires_fr', 'tires_rr', 'tires_rl'])
        a_list = []
        with open(self.misc_csv_location) as csvfile:
            reader = csv.reader(csvfile,delimiter=",")
            for row in reader:
                c = telemetry(float(row[0]),float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5]),float(row[6]),float(row[7]),float(row[8]),float(row[9]), float(row[10]), float(row[11]), float(row[12]), float(row[13]), float(row[14]), float(row[15]))
                a_list.append(c)
                    
        return a_list

