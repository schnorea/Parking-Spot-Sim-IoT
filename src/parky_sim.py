# IoT Parking Meter Simulation
# By Aussie Schnore

import random
import datetime
import time
import math
from pprint import pprint

from randomgroup import group_list

parking_config = [
    {
        "address": "95085 Florencio Lights, XYZ, AB",
        "location": [
            "-75.5712",
            "-130.5355"
        ],
        "meter_count": 5
    },
    {
        "address": "15275 Elfrieda Street, XYZ, AB",
        "location": [
            "-48.8712",
            "-151.6866"
        ],
        "meter_count": 5
    },
    {
        "address": "76229 Eveline Pass, XYZ, AB",
        "location": [
            "61.9100",
            "29.3380"
        ],
        "meter_count": 1
    },
    {
        "address": "253 Johnson Creek, XYZ, AB",
        "location": [
            "-87.7160",
            "-176.5731"
        ],
        "meter_count": 5
    },
    {
        "address": "3243 Bethany Loop, XYZ, AB",
        "location": [
            "-61.5722",
            "-146.2923"
        ],
        "meter_count": 2
    },
    {
        "address": "069 Aufderhar Causeway, XYZ, AB",
        "location": [
            "23.1485",
            "-139.9646"
        ],
        "meter_count": 5
    },
    {
        "address": "190 Seth Ways, XYZ, AB",
        "location": [
            "-12.8557",
            "-165.1071"
        ],
        "meter_count": 1
    },
    {
        "address": "36590 Reanna Canyon, XYZ, AB",
        "location": [
            "-45.9565",
            "-4.1794"
        ],
        "meter_count": 2
    },
    {
        "address": "093 Harris Parkway, XYZ, AB",
        "location": [
            "-32.8645",
            "25.9577"
        ],
        "meter_count": 3
    },
    {
        "address": "44712 Rau Loaf, XYZ, AB",
        "location": [
            "-20.3352",
            "-177.8691"
        ],
        "meter_count": 2
    }
]



SECONDS_PER_HOUR = 60 * 60
SECONDS_PER_MINUTE = 60

# The percent of the total parking spots occupied each hour starting at 0000 to 2300 local time.
# Derived from Figure 4 in this document
# Parking Study - Village of Arlington Heights - Draft Report
# http://p1cdn4static.civiclive.com/UserFiles/Servers/Server_7230689/File/Our%20Community/VillageProjects/Parking%20Study.pdf
percent_occupied_table = [37.54,
                         31.96,
                         27.86,
                         27.70,
                         27.50,
                         27.30,
                         27.32,
                         27.37,
                         32.29,
                         36.55,
                         45.08,
                         52.62,
                         55.40,
                         57.70,
                         56.23,
                         52.29,
                         51.15,
                         60.16,
                         68.69,
                         74.59,
                         80.00,
                         75.08,
                         60.49,
                         45.73]


# Example of object returned by IoT meter system
# this format is set in the Spot class
"""
{
	"timestamp": 1519518300,
	"isOccupied": true,
	"meter": {
		"number": 1,
		"location": ["-75.5712", "-130.5355"],
		"address": "95085 Florencio Lights, XYZ, AB"
	}
}
"""


# Class that maintains the state of a parking spot and produces
# the IoT message object
class Spot(object):
    def __init__(self, address, location, number, isOccupied):
        self.address = address
        self.location = location
        self.number = number
        self.isOccupied = isOccupied

    def occupy(self):
        self.isOccupied = True

    def empty(self):
        self.isOccupied = False

    def produce(self, timestamp):
        result = {}
        result['timestamp'] = timestamp
        result['isOccupied'] = self.isOccupied
        meter = {}
        meter['number'] = self.number
        meter['location'] = self.location
        meter['address'] = self.address
        result['meter'] = meter
        return result

# Class that maintains the state of the entire Parking system
class Parking(object):
    def __init__(self, conn, parking_config, percent_occupied_table, timestamp, ext_callback):
        self.parking_config = parking_config
        self.conn = conn  # meant to hold the mqtt_connect and to feed it to callback
        self.percent_occupied_table = percent_occupied_table
        self.start_timestamp = timestamp
        self.ext_callback = ext_callback
        self.current_percent_occupied,_ = self._percent_occupied_trend_epoch(timestamp)
        self.spots = []
        self.spots_cnt = 0
        self._make_spots()
        self._re_report_schedule()
        self.pause = 0.01  # Sets the time.sleep value between call_backs
 
    def timestamp_to_local_mil_time(self, timestamp):
        # given an epoch timestamp convert to local 24 hour time
        datetime_time = datetime.datetime.fromtimestamp(timestamp)
        result = (datetime_time.hour * 100) + datetime_time.minute
        return result

    def _re_report_schedule(self):
        # Calculates when spots should report in.  This reporting is in addition
        # to reporting state change from occupied to empty to occupied
        report_order = list(range(len(self.spots)))
        random.shuffle(report_order)
        # Once per hour starting at minute intervals starting at self.start_timestamp
        self.re_report_schedule_list = group_list(report_order, 60)

    def _call_back(self, obj, mil_hour, source=""):
        self.ext_callback(self.conn, obj, mil_hour, source)
        time.sleep(self.pause)

    def _percent_occupied_trend_epoch(self, timestamp):
        mil_hour = self.timestamp_to_local_mil_time(timestamp)
        return self._percent_occupied_trend_hr(mil_hour)
        
    def _percent_occupied_trend_hr(self, mil_hour):
        # Using the 'percent_occupied_table' and based on the time of day
        # look up what the percent occupancy is for all parking spots
        if mil_hour < 0 or mil_hour > 2359:
            # Error
            # TODO: Raise Exception. For now print out error and exit
            print(f"ERROR: Function percent_occupied was called with a mil_hour that was out of range {mil_hour}. Exiting...")
            exit(1)
        # Interpolate percentage
        hour, minutes = divmod(mil_hour, 100)

        next_hour = hour + 1
        if next_hour > 23:
            # Wrap at midnight case
            next_hour = 0
        frac_hour = minutes/60
        pcnt_start_hour = self.percent_occupied_table[hour]
        pcnt_end_hour = self.percent_occupied_table[next_hour]
        pcnt_delta = pcnt_end_hour - pcnt_start_hour
        pcnt_frac = pcnt_delta * frac_hour
        pcnt_occupied = pcnt_start_hour + pcnt_frac
        return pcnt_occupied, pcnt_delta

    def _make_spots(self):
        # Instances the spot object and sets the initial spot occupancy
        for lot in self.parking_config:
            meter_count = lot['meter_count']
            for i in range(meter_count):
                address = lot['address']
                location = lot['location']
                number = i + 1
                isOccupied = False
                spot = Spot(address, location, number, isOccupied)
                self.spots.append(spot)
        # Given the current time stamp calc the percent occupied that should
        # be prepopulated
        mil_hour = self.timestamp_to_local_mil_time(self.start_timestamp)
        pcnt_occupied,_ = self._percent_occupied_trend_hr(mil_hour)
        pop_size = len(self.spots)
        self.spots_cnt = pop_size
        pick_size = int(pop_size * (pcnt_occupied/100.0))
        # Pick spots 
        occ_spots = random.sample(self.spots, pick_size)
        for spot in occ_spots:
            # Set spot occupied
            spot.occupy()

    def percent_occupied(self):
        # Returns percent occupied
        pop_size = len(self.spots)
        occupied = 0
        for a in self.spots:
            if a.isOccupied:
                occupied += 1
        pcnt_occupied = (occupied/pop_size) * 100.0
        return pcnt_occupied

    def _get_full(self):
        result = []
        for spot in self.spots:
            # Set spot occupied
            if spot.isOccupied:
                result.append(spot)
        return(result)

    def _get_empty(self):
        result = []
        for spot in self.spots:
            # Set spot occupied
            if not spot.isOccupied:
                result.append(spot)
        return(result)

    def _swap_full_empty(self, number_to_swap, timestamp):
        # Take empty and full spots and swap them to simulate background activity
        # that doesn't change the occupancy percentage (no more than 29 at a time)
        # trying to do all the swaps in under a minute
        full_spots = self._get_full()
        number_full = len(full_spots)
        empty_spots = self._get_empty()
        number_empty = len(empty_spots)
        # Calc the number we can swap
        # 29 should be the max as we want to empty a spot and fill it at different
        # times within a one minute window
        number_can_swap = min([number_full, number_empty, number_to_swap, 29])
        spots_to_empty = random.sample(full_spots, number_can_swap)
        spots_to_fill = random.sample(empty_spots, number_can_swap)
        # Okay we have 58 seconds to do this lets make it look good
        seconds_to_swap = random.sample(range(58), number_can_swap * 2)
        seconds_to_swap.sort()
        empty_now = False
        empty_first = False
        # Give it some randomness
        if len(seconds_to_swap) % 2 == 0:
            empty_now = True
            empty_first = True
        # Debug
        # print(len(seconds_to_swap),len(spots_to_fill),len(spots_to_empty))
        for sec in seconds_to_swap:
            cur_timestamp = timestamp + sec
            if not empty_now:
                spot_empty = spots_to_fill.pop()
                spot_empty.occupy()
                mil_time = self.timestamp_to_local_mil_time(cur_timestamp)
                self._call_back(spot_empty.produce(cur_timestamp), mil_time, "Swap")
                empty_now = True
            elif empty_now:

                spot_fill = spots_to_empty.pop()
                spot_fill.empty()
                mil_time = self.timestamp_to_local_mil_time(cur_timestamp)
                self._call_back(spot_fill.produce(cur_timestamp), mil_time, "Swap")
                empty_now = False

    def _simulate_even_spot_swaps(self, timestamp):
        spots_currently_occupied = self.spots_cnt * (self.percent_occupied()/100.0)
        spots_cnt_to_swap = int(spots_currently_occupied * 0.1)
        if spots_cnt_to_swap > 0:
            self._swap_full_empty(spots_cnt_to_swap, timestamp)

    def _simulate_spot_occupancy(self, timestamp):
        # Here we make changes to the spot occupancy rate in line with what is 
        # called out in the "percent_occupied_table"
        pcnt_new, _ = self._percent_occupied_trend_epoch(timestamp)
        # Calc the number of spots that should be occupied
        spots_should_be_occupied = self.spots_cnt * (pcnt_new/100.0)
        # Get the number that are currently occupied
        spots_currently_occupied = self.spots_cnt * (self.percent_occupied()/100.0)
        # Calc the change needed to make 
        spots_to_change = math.floor(spots_should_be_occupied - spots_currently_occupied)
        #print(f"spots_to_change {spots_to_change}")
        choose_cnt_to_fill = 0
        choose_cnt_to_empty = 0
        if spots_to_change >= 1.0:
            # if here need to take empty spots and fill them
            # get the number of empty spots to fill
            choose_cnt_to_fill = spots_to_change
            # Get just the empty spots
            empty_spots = self._get_empty()
            # Sample those spots
            if len(empty_spots) < choose_cnt_to_fill:
                # not enough spots left to sample just take what is left
                choose_cnt_to_fill = len(empty_spots)
            spots_to_fill = random.sample(empty_spots, choose_cnt_to_fill)
            for spot in spots_to_fill:
                mil_time = self.timestamp_to_local_mil_time(timestamp)
                spot.occupy()
                self._call_back(spot.produce(timestamp), mil_time, "Grow")
        elif spots_to_change > -1.0 and spots_to_change < 1.0:
            # Not enough change yet to get even a single spot
            # Another way of saying this is that there may not be 
            # enough whole spots to fill or empty yet.
            pass
        else:
            # if here need to take full spots and empty them
            # get the number of full spots to empty
            choose_cnt_to_empty = abs(spots_to_change)
            # Get just the full spots
            full_spots = self._get_full()
            # Sample those spots
            if len(full_spots) < choose_cnt_to_empty:
                # not enough spots left to sample just take what is left
                choose_cnt_to_empty = len(full_spots)
            spots_to_empty = random.sample(full_spots, choose_cnt_to_empty)
            for spot in spots_to_empty:
                mil_time = self.timestamp_to_local_mil_time(timestamp)
                spot.empty()
                self._call_back(spot.produce(timestamp), mil_time, "Shrink")

    def _simulate_re_report(self, timestamp):
        # Along with reporting when the state of a spot changes, the IoT devices 
        # monitoring the parking lot spots are configured to report in
        # at a regular interval 
        _, minute_of_the_hour = divmod(self.timestamp_to_local_mil_time(timestamp),100)
        reporting_now_list = self.re_report_schedule_list[minute_of_the_hour]
        for spot_index in reporting_now_list:
            if spot_index > -1:
                obj = self.spots[spot_index].produce(timestamp)
                mil_time = self.timestamp_to_local_mil_time(timestamp)
                self._call_back(obj, mil_time, "Report")


    def walk_through_sim(self, hours_to_simulate):
        # Here we call the functions that simulate change in spot occupancy
        walk_minutes = int(hours_to_simulate * 60)
        
        for minute in range(walk_minutes):
            # Calc the next timestamp
            walk_current_epoch = self.start_timestamp + (minute * SECONDS_PER_MINUTE)

            # Simulates the increase in decrease in parking spot occupancy
            self._simulate_spot_occupancy(walk_current_epoch)

            # Simulates regular node reporting
            self._simulate_re_report(walk_current_epoch)

            # Simulates the spots swaps that don't effect the overall occupancy
            self._simulate_even_spot_swaps(walk_current_epoch)


if __name__ == "__main__":
    # Testing Callback
    def just_print(conn, obj, mil_time, source=""):
        print(mil_time, source)
        pprint(obj)
        #print()

    # Example of usage
    timestamp = 1571005498
    # This to data structures are defined in this module but they could be feed from outside
    # parking_config
    # percent_occupied_table
    parking = Parking(None, parking_config, percent_occupied_table, timestamp, just_print)
    print()
    print()
    hours_to_simulate = 24
    parking.walk_through_sim(hours_to_simulate)





