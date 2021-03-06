# AWS CMS Enablement

This repo contains several scripts necessary to automate the creation of devices in Connected Mobility Solution


# Requirements

1. The [AWS Connected Mobility Solution](https://github.com/aws-solutions/aws-connected-mobility-solution) was deployed successfully.

2. An AWS CLI profile is setup that has administrator access to the account where CMS is deployed.  This account will be referenced in the script parameters as "profile"

3. A valid VIN will be used as the AWS IoT Core Thing Name and subsequent simulations

Note: If you see "The security token included in the request is invalid" error for CreateRole, make sure your security credentials are properly configured for the IAM user that was created and you are not using the root/default credentials.

# Credentials

Before you can deploy an application, be sure you have credentials configured. If you have previously configured your machine to run boto3 (the AWS SDK for Python) or the AWS CLI then you can skip this section. If you used Cloud9 as a deployment mechanism, you can use the default profile.

If this is your first time configuring credentials for AWS you can follow these steps to quickly get started:

$ mkdir ~/.aws
$ cat >> ~/.aws/config
[default]
aws_access_key_id=YOUR_ACCESS_KEY_HERE
aws_secret_access_key=YOUR_SECRET_ACCESS_KEY
region=YOUR_REGION (such as us-west-2, us-west-1, etc)

If you want more information on all the supported methods for configuring credentials, see the boto3 docs.

# Setup your environment

1. Clone this repo to your local machine or Cloud9 environement

```
git clone https://github.com/aws-samples/aws-cms-telemetry-demo.git
```

2. Install the requirements.txt to install the prequresits.

```
cd aws-cms-telemetry-demo/
pip3 install -r requirements.txt
```

# Overview

The setupSingleVehicle.py will perform all the necessary steps to create a single vehicle in CMS.  The script uses the CloudFormation template exports to build the necessary API endpoints, get the necessary certificateIds and user credentials needed to make changes.

Run the following script to register a single vehicle:

```bash
./setupSingleVehicle.py --profile=default --stackName=cms-development --VIN=LSH14J4C4LA046511 --FirstName=CMS --LastName=User --Username=testCMSUser1 --Password=Testing1234 --CDFstackName cdf-core-development
```

| parameter      | short | description                                                           |
|----------------|-------|-----------------------------------------------------------------------|
| --profile      | -p    | the profile to use                                                    |
| --stackName    | -s    | the CMS stack name                                                    |
| --CDFstackName | -c    | the CDF stack name                                                    |
| --FirstName    | -f    | Owner given name                                                      |
| --LastName     | -l    | Owner family name                                                     |
| --VIN          | -v    | any VIN number you want (will be the Thing name                       |
| --Username     | -u    | the admin user name provided during setup (CMS confirmation mail)     |
| --Password     | -pwd  | the admin password generated during setup (CMS confirmation mail)     |
| --SkipSetupProvisioningTemplates     | -skip  | this will skip setting up provisioning templates if you want to setup multiple devices (bool)     |
| --GenerateCSR     | -csr  | this will generate a csr/private key on the device rather than allow IoT Core to generate     |

1. The script will first make modifications to the Cognito User Pool created by default by the CMS CF template.  This will allow for automated creation of users and authentication, rather than a manual method via the Cognito front-end

2. The script will then take this cognito client Id and pass it into CMS APIs to authenticate to those front-end APIs

3. From here, we now need to follow the setup process for a vehicle, which is the following:
    1. Create a device supplier 
    2. Register a device (TCU, ECU, etc)
    3. Activate a device
    4. Assosciate a device to a user

4. At this point, we have created a CMS user and created a single vehicle.  The next step is provisioning certificates to the device such that it can connect to IoT Core

5. To create device certificates for a fleet, we will use Fleet Provisioning Templates with just-in-time provisioning (JITP) which provides a bootstrap certificate to place on the device during manufacturing.  This certificate will allow the device to connect and subscribe to reserved IoT Core topics which will then provision the production certificate for the device.

6. When the device connects to this reserved topic a new certificate and public/private key is generated and downloaded to the device.  The device then uses that combination to subscribe to CMS topics.  For this demo, we will use virtual devices, essentially a directory with a unique vehicle Id (VIN) and the public/private certificate in the project folder

7. When running the setupSingleVehicle.py script, it will attempt to publish a single telemetry object to the /dt/cvra/+/data topic which is where telemetry data for the vehicle is published.  This initial load of data is necessary to show your vehicle in the UI.  After running the script, the output should show the cloudfront UI URL and the user can click to login with the user they created in the script.

Sample output:
```
Vehicle setup sucessfully, please visit http://d3lqxcqk33ijcr.cloudfront.net to login with your user and see your vehicle
```

8. From there, we can use the generateTelemetry.py to create payloads for devices generating routes and simulating vehicle traffic within the UI.

# Creating your Device

1. To generate telemetry, we can use the generate telemetry script, which will take the VIN that was just used to create some telemetry from the latlong2.csv
```
./generateTelemetry.py --VIN LSH14J4C4KA097044 --profile=default
```
2. This should post telemetry data (latitude/longitude) to the proper topic every second from the latLong2.csv file.  This data is generated using google maps and other routes can be generated if the below steps are followed.

3. Upon execution, you should see outputs like the below and your vehicle icon should be moving on the screen.

```
Generating Trip ID of 09ec10c7310d44d988cfb0ff5cdb3b98                                                                            Begin publishing trip data.  Will Begin publishing trip data.  Will publish 248 payloads
Successfully published coordinates Coords(x=33.77521, y=-84.39609) of 248
Successfully published coordinates Coords(x=33.77521, y=-84.39606) of 248
Successfully published coordinates Coords(x=33.77521, y=-84.39605) of 248
```

# Create some telemetry

To create a CSV of lat/long coordinates to create a proper simulation of a vehicle along a route, the quickest implementation is to utilize an online maps resource and export a route.  This will provide the most accurate data to simulate your trips and begin build upon other features available in CMS.  Below is the procedure to develop that data to be stored in assets/latLong.csv as exported.

    1. Go to maps.google.com 
    2. Click on the hamburger menu and select 'Your Places'
    3. At the bottom of the sidebar, select 'CREATE MAP'
    4. When the map creation interface loads in a new tab, click the 'Add directions' under the search bar
    5. Put in two local landmarks in the city of your choice and the route should appear on the map
    6. Click on the 'Untitled Map' dot menu, and select 'Export to KML/KMZ'
    7. Select the dropdown and select just the route directions and select download.
    8. Find the Placemark/coordinates within the markup language and copy that section (without the tags) into your latLong.csv


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

