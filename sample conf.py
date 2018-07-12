# CONFIGURATION FILE
# set the parameters unique to your setup below
# then rename this file to "conf.py"

# for handling projections
from functools import partial
import pyproj

# this must be a meter-based projection appropriate for your region
# UTM projections are suggested. 
PROJECT_EPSG = 26759 # look up on https://www.epsg-registry.org/

conf = {
	# PostgreSQL database connnection
	'db':
		{
			'host':'localhost',
			'name':'db1', # database name
			'user':'minhpham',
			'password':'123456',
			'tables':{
				# these are SQL-safe table names used directly in queries
				# if you set up the tables with create_nb_tables.sql, you have likely changed the prefix
				'trips':'psta_trips',
				'stops':'psta_stops',
				'stop_times':'psta_stop_times',
				'directions':'psta_directions'
			}
		},
	# agency tag for the Nextbus API, which can be found at
	# http://webservices.nextbus.com/service/publicXMLFeed?command=agencyList
	'agency':'psta',
	# Where is the ORSM server? Give the root url
	'OSRMserver':{
		'url':'http://localhost:5002',
		'timeout':10 # seconds
	},
	'min_OSRM_match_quality':0.3,
	# function for projecting from lat-lon for shapely
	# http://toblerity.org/shapely/manual.html#other-transformations
	# http://all-geo.org/volcan01010/2012/11/change-coordinates-with-pyproj/
	'projection':partial(
		 pyproj.transform,
		 pyproj.Proj('+init=EPSG:4326'),
		 pyproj.Proj('+init=EPSG:'+str(PROJECT_EPSG))
	),
	'localEPSG':PROJECT_EPSG,
	# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
	# This must be an unabreviated timezone name to allow postgresql to account 
	# for daylight savings time.
	'timezone': 'America/Toronto',
	# distance threshold for stop matching in meters; stops more than this far 
	# away from the matched route will not be included
	'stop_dist':30,
	# estimated GPS error radius in meters
	# this applies to all points and effects map-matching
	# higher values include more potential matches but take longer to process
	'error_radius':20,
    'API_URL': "http://transit.jadorno.com"
}
