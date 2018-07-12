import sys
sys.path.append("..") # Adds higher directory to python modules path.
import requests, numpy, sys, db, pandasql, conf, warnings
from pandas.core.frame import DataFrame

    
""" These functions will use GRTFS API to create GTFS tables"""
def GetAllRoutes(request_time):
    """ get all route_id's from agency"""
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    try:
        APICall = (URL + "/" + 
                   agency + "/" +
                   "gtfs/" +
                   "routes?timestamp=" + repr(request_time)
                   )
        Response = requests.get(APICall)
    except Exception as e:
        print('API problem: ' + e)
        return
    # response received, check if status is ok
    ResponseParse = Response.json()
    if ResponseParse['header']['status'] != 'OK':
        print('problem with API call: ' + APICall)
        return
    # get all routes
    routes = DataFrame(ResponseParse['data'])
    return {'routes': routes, 'timestamp': ResponseParse['header']['timestamp']}

def GetAllTrips(routes, request_time):
    """Get all trips from given route_id's"""
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    Total = len(routes.route_id)
    count = 0
    print("Total routes: {0}".format(Total))
    
    for route_id in routes.route_id:
        count = count + 1;
        # progress status
        if count*100/Total % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(count*100/Total))
            sys.stdout.flush()
        try:
            APICall = (URL + "/" + 
                       agency + "/" +
                       "gtfs/" +
                       "trips" + 
                       "?timestamp=" + repr(request_time) +
                       "&route_id=" + route_id.encode("ascii")
                       )
            Response = requests.get(APICall)
        except Exception as e:
            print('API problem: ' + e)
            return
        # response received, check if status is ok
        ResponseParse = Response.json()
        if ResponseParse['header']['status'] != 'OK':
            warnings.warn('problem with API call: '+ APICall, stacklevel = 3)
            continue
        # append trip_id
        trip_data = DataFrame(ResponseParse['data']['trips'])
        trip_data['route_id'] = route_id.encode("ascii")
        if 'trips' not in locals():
            trips = trip_data
        else:
            trips = trips.append(trip_data)
    return trips
            

def GetAllStopTImes(trips, request_time):
    """Get all stop times from an agency given trip_id's"""
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    # get all stops by matching trip_id with stop_times table
    Total = len(trips.trip_id)
    count = 0
    print("Total trips: {0}".format(Total))
    
    for trip_id in trips.trip_id:
        count = count + 1
        # progress status
        if count*100/Total % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(count*100/Total))
            sys.stdout.flush()
        try:
            APICall = (URL + "/" + 
                       agency + "/" +
                       "gtfs/" +
                       "stop_times" + 
                       "?timestamp=" + repr(request_time) +
                       "&trip_id=" + trip_id.encode("ascii")
                       )
            Response = requests.get(APICall)
        except Exception as e:
            print('API problem: ' + e)
            return
        # response received, check if status is ok
        ResponseParse = Response.json()
        if ResponseParse['header']['status'] != 'OK':
            warnings.warn('problem with API call: '+ APICall, stacklevel = 3)
            continue
        # append trip_id
        stop_data = DataFrame(ResponseParse['data']['stops'])
        stop_data['trip_id'] = trip_id.encode("ascii")
        if 'stop_times' not in locals():
            stop_times = stop_data
        else:
            stop_times = stop_times.append(stop_data)
    return stop_times

def GetAllStops(stop_times, request_time):
    """Get stops info from an agency given stop_times table by using /stops API call"""
    URL = conf.conf['API_URL']
    agency = conf.conf['agency']
    stops = list()
    Total = len(numpy.unique(stop_times.stop_id))
    count = 0
    print("Total stops: {0}".format(Total))

    for stop_id in numpy.unique(stop_times.stop_id):
        count = count + 1
        # progress status
        if count*100/Total % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(count*100/Total))
            sys.stdout.flush()

        try:
            APICall = (URL + "/" + 
                       agency + "/" +
                       "gtfs/" +
                       "stops" + 
                       "?timestamp=" + repr(request_time) +
                       "&stop_id=" + stop_id.encode("ascii")
                       )
            Response = requests.get(APICall)
        except Exception as e:
            print('API problem: ' + e)
            return
        # response received, check if status is ok
        ResponseParse = Response.json()
        if ResponseParse['header']['status'] != 'OK':
            warnings.warn('problem with API call: '+ APICall, stacklevel = 3)
            continue
        # parse response into stops
        try: 
            stop_name = ResponseParse['data']['properties']['stop_name']
        except: stop_name  = ''
        try:
            stop_code = ResponseParse['data']['properties']['stop_code']
        except: stop_code = ''
        try: 
            lon = ResponseParse['data']['coordinates'][0][0]
        except: lon = ''
        try: 
            lat = ResponseParse['data']['coordinates'][0][1]
        except: lat = ''
        uid = count
        report_time = repr(request_time)
        
        stops.append({'stop_name':stop_name,
                         'stop_id':stop_id,
                         'stop_code':stop_code,
                         'lon':lon, 
                         'lat':lat, 
                         'uid':uid, 
                         'report_time':report_time})
    return DataFrame(stops)

""" These functions format data and store to database"""
def StoreStops(stops):
    count = 0
    Total = len(stops.index)
    for index, row in stops.iterrows():
        # progress status
        count = count + 1
        if count*100/Total % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(count*100/Total))
            sys.stdout.flush()
        # store data
        db.try_storing_stop(row['stop_id'],
                            row['stop_name'],
                            row['stop_code'],
                            row['lon'],
                            row['lat'])
        
def StoreDirections(trips, stop_times):
    Directions = pandasql.sqldf(
            """
            select trips.route_id, trips.direction_id, trip_stops.stops
            from trips left join
                (SELECT trip_id, group_concat(stop_id) as stops
                FROM stop_times
                GROUP BY trip_id) as trip_stops
            on trips.trip_id = trip_stops.trip_id
            group by trips.route_id, trips.direction_id, trip_stops.stops
            """,
            locals()
    )
    count = 0
    Total = len(Directions.index)
    for index, row in Directions.iterrows():
        # progress status
        count = count + 1
        if count*100/Total % 2 == 0:
            sys.stdout.write("\r" + "progress: {0}%".format(count*100/Total))
            sys.stdout.flush()
        # store data
        db.try_storing_direction(route_id = row.route_id, 
                                 did = row.direction_id, 
                                 title = '', name = '', branch = '', useforui = 'f',
                                 stops = '{' + str(row.stops) + '}'
                                 )