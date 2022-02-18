# Parking-Spot-Sim-IoT

Parking spots are simulated to model the changes in spot occupancy expected during a day.

# Define a Parking System
A parking lot is defined as having a common address and location but having multiple metered spots.
The simulator allows the creatation of multiple parking lots. A sample set of lots and metered spots is provided in the code.

# Define an Occupancy Percentage Table
To mimic the flow of traffic and the use of spots across the day a table is defined in the code that has a per hour occupancy percentage. This percentage is for all the parking lots in the simulation.  Future work might make a table per lot.  A sample of the table is in the code.

# Call Back
As the simulation progresses the actions of a spot being occupied or filled and emptied call a call_back.  The call back can be used to print out the event or to call a routine to transmitt the action via MQTT or other to a IoT Hub or IoT Core like broker.  Included in the code is an example of this targeting the AWS Cloud IoT connectivity through the IoT Python SDK.  You will need to install this and get the required credentials to use it.

