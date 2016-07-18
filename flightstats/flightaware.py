# encoding: utf-8
'''
Created on May 18, 2016

@author: tal

Docs are here: https://flightaware.com/commercial/flightxml/documentation2.rvt

'''
from __future__ import unicode_literals, division, print_function, absolute_import

import os
from pprint import pprint
import datetime
import calendar
from pytz import timezone as pytz_timezone

import requests
from flightstats.airports_icao_to_iata import AIRPORTS_IATA_TO_ICAO, AIRPORTS_ICAO_TO_IATA
from flightstats.flightaware_airports import AIRPORTS as FA_AIRPORTS

DEFAULT_NUMBER_OF_SEARCH_RESULTS = 5

USERNAME = os.environ['FLIGHTAWARE_USERNAME']
API_KEY = os.environ['FLIGHTAWARE_API_KEY']
URL = "http://flightxml.flightaware.com/json/FlightXML2/"

def flight_aware(command, params):
    """call a flight aware API"""
    res = requests.get(URL + command, auth=(USERNAME, API_KEY), params=params, timeout=10)
    if res.status_code == requests.codes.ok:  # @UndefinedVariable pylint:disable=no-member
        return res.json()

def airport_info(airport_code):
    """Get airport info
        {'AirportInfoResult': {'latitude': 40.6399257, 'timezone': ':America/New_York',
         'name': 'John F Kennedy Intl', 'longitude': -73.778695, 'location': 'New York, NY'}}
    """
    params = dict(airportCode=airport_code)
    return flight_aware("AirportInfo", params)

def flight_info_extended(faFlightID , departure_date=None, arrival_date=None):
    """Extended flight info base on flightaware flight ID

    Example: flight_info_extended("QTR1", departure_date=datetime.date(2016, 6, 14))
    Example: flight_info_extended("DAL2824-1463808481-airline-0168")

    Response example:
        {'FlightInfoExResult':
            {'flights': [{ 'actualarrivaltime': 0,
                           'actualdeparturetime': 0,
                           'aircrafttype': 'A320',
                           'destination': 'MDSD',
                           'destinationCity': 'Punta Caucedo',
                           'destinationName': 'Las Americas',
                           'diverted': '',
                           'estimatedarrivaltime': 1464025020,
                           'faFlightID': 'JBU509-1463808444-airline-0037',
                           'filed_airspeed_kts': 460,
                           'filed_airspeed_mach': '',
                           'filed_altitude': 350,
                           'filed_departuretime': 1464011700,
                           'filed_ete': '03:32:00',
                           'filed_time': 1463808444,
                           'ident': 'JBU509',
                           'origin': 'KJFK',
                           'originCity': 'New York, NY',
                           'originName': 'John F Kennedy Intl',
                           'route': 'SHIPP LINND ROLLE ATUGI L454 GOUGH L454 LUCTI L454 MNDEZ M594 CERDA L453 ASIVO W37 KOBET G446 KERSO'}],
            'next_offset': -1}}

    """
    params = dict(ident=faFlightID)
    result = flight_aware("FlightInfoEx", params)
    if departure_date or arrival_date:
        flight_info_result = result.get('FlightInfoExResult')
        if flight_info_result and isinstance(flight_info_result, dict):
            flights = flight_info_result.get('flights')
            if flights and isinstance(flights, list):
                if departure_date:
                    flights = [flight for flight in flights
                               if datetime.datetime.fromtimestamp(flight.get('filed_departuretime')).date() == departure_date]
                if arrival_date:
                    flights = [flight for flight in flights
                               if datetime.datetime.fromtimestamp(flight.get('estimatedarrivaltime')).date() == arrival_date]
                result["FlightInfoExResult"]["flights"] = flights
    return result

def flight_airline_info(faFlightID):
    """
        returns airline flight info for flightaware flight id
        {'AirlineFlightInfoResult': {'bag_claim': '',
                              'codeshares': [],
                              'faFlightID': 'JBU509-1463808444-airline-0037',
                              'gate_dest': 'B3',
                              'gate_orig': '25',
                              'ident': 'JBU509',
                              'meal_service': '',
                              'seats_cabin_business': 0,
                              'seats_cabin_coach': 150,
                              'seats_cabin_first': 0,
                              'tailnumber': '',
                              'terminal_dest': '',
                              'terminal_orig': ''}}

    """
    params = dict(faFlightID=faFlightID)
    return flight_aware("AirlineFlightInfo", params)

def find_flights(flight_number):
    """
        response example:
        {'FlightInfoExResult': {'flights': [{'actualarrivaltime': 0,
                                       'actualdeparturetime': 0,
                                       'aircrafttype': 'A320',
                                       'destination': 'MDSD',
                                       'destinationCity': 'Punta Caucedo',
                                       'destinationName': 'Las Americas',
                                       'diverted': '',
                                       'estimatedarrivaltime': 1464197820,
                                       'faFlightID': 'JBU509-1463981207-airline-0101',
                                       'filed_airspeed_kts': 383,
                                       'filed_airspeed_mach': '',
                                       'filed_altitude': 0,
                                       'filed_departuretime': 1464184500,
                                       'filed_ete': '03:32:00',
                                       'filed_time': 1463981207,
                                       'ident': 'JBU509',
                                       'origin': 'KJFK',
                                       'originCity': 'New York, NY',
                                       'originName': 'John F Kennedy Intl',
                                       'route': ''},],
                         'next_offset': -1}}

    """
    params = dict(ident=flight_number, howMany=15)
    return flight_aware("FlightInfoEx", params)

def airline_info(icao_code):
    """Get the airline info for a specific ICAO code
    Example of a reply for QTR:
    {u'AirlineInfoResult': {u'callsign': u'Qatari',
                        u'country': u'Qatar',
                        u'location': u'Doha',
                        u'name': u'Qatar Airways Company',
                        u'phone': u'+1-866-728-2748',
                        u'shortname': u'Qatar Airways',
                        u'url': u'http://www.qatarairways.com/'}}
    """
    params = dict(airlineCode=icao_code)
    return flight_aware("AirlineInfo", params)

def find_next_flight(flight_number):
    """
        in flight info response:
        {'InFlightInfoResult': {'altitude': 0,
                         'altitudeChange': '',
                         'altitudeStatus': '',
                         'arrivalTime': 0,
                         'departureTime': 0,
                         'destination': 'MDSD',
                         'faFlightID': 'JBU509-1463808444-airline-0037',
                         'firstPositionTime': 0,
                         'groundspeed': 0,
                         'heading': 0,
                         'highLatitude': -200.0,
                         'highLongitude': -200.0,
                         'ident': 'JBU509',
                         'latitude': 0.0,
                         'longitude': 0.0,
                         'lowLatitude': 200.0,
                         'lowLongitude': 200.0,
                         'origin': 'KJFK',
                         'prefix': '',
                         'suffix': '',
                         'timeout': 'timed_out',
                         'timestamp': 0,
                         'type': 'A320',
                         'updateType': '',
                         'waypoints': '40.64 -73.78 40.62 -73.75 40.61 -73.72 40.6 -73.71 40.59 -73.7 40.58 -73.68 40.58 -73.67 40.57 -73.66 40.56 -73.64 40.55 -73.63 40.55 -73.62 40.54 -73.6 40.53 -73.6 40.53 -73.59 40.52 -73.57 40.51 -73.56 40.51 -73.55 40.49 -73.52 40.49 -73.52 40.39 -73.34 40.33 -73.25 40.08 -72.83 40.08 -72.82 39.87 -72.46 39.83 -72.4 39.74 -72.26 39.7 -72.19 39.57 -71.98 39.41 -71.71 37.99 -71.71 37.52 -71.71 37.39 -71.71 36.95 -71.66 35.64 -71.53 34.67 -71.28 34.18 -71.16 34.01 -71.12 33.69 -71.04 31.44 -70.5 30.37 -70.25 27.76 -69.68 26.72 -69.45 25.01 -69.1 25 -69.09 24.97 -69.09 24.68 -69.02 24.4 -68.95 23.58 -68.75 23.46 -68.91 23.34 -69.08 23.22 -69.24 22.75 -69.9 22.57 -69.89 22.39 -69.87 22.03 -69.85 21.73 -69.82 21.36 -69.8 20.94 -69.77 20.63 -69.74 20.59 -69.74 20.44 -69.73 20.29 -69.72 20.24 -69.71 20.18 -69.71 20.12 -69.7 19.96 -69.69 19.96 -69.69 19.96 -69.69 19.94 -69.69 19.7 -69.71 19.46 -69.72 19.27 -69.71 19.23 -69.71 19.07 -69.7 19.05 -69.7 18.85 -69.69 18.69 -69.68 18.68 -69.68 18.6 -69.67 18.52 -69.67 18.43 -69.67'}}

    """
    params = dict(ident=flight_number)
    return flight_aware("InFlightInfo", params)

def search(destination=None, origin=None, number_of_results=None):
    """Generic search!"""
#     query = "-belowAltitude 100 -aboveGroundspeed 200"
#     query = "-idents QTR*"
#     query = "-originOrDestination OTHH"
#     query = "-destination OTHH"
    queries = []
    if destination:  # icao code
        queries.extend(["-destination", destination])
    if origin:  # icao code
        queries.extend(["-origin", origin])
    query = " ".join(queries)
    print(query)
    number_of_results = number_of_results or DEFAULT_NUMBER_OF_SEARCH_RESULTS  # Must be a positive integer value less than or equal to 15
    params = dict(query=query, howMany=number_of_results, offset=0)
    return flight_aware("Search", params)

def departures(airport_code, number_of_results=15):
    """fetch departures - this function is costly"""
    if airport_code:
        icao = AIRPORTS_IATA_TO_ICAO.get(airport_code)
        results = search(origin=icao, number_of_results=number_of_results)
        if results and isinstance(results, dict):
            search_results = results.get('SearchResult')
            if search_results and isinstance(search_results, dict):
                aircraft = search_results.get('aircraft')
                if aircraft and isinstance(aircraft, list):
                    for an_aircraft in aircraft:
                        destination = an_aircraft.get('destination')
                        if destination:
                            iata = AIRPORTS_ICAO_TO_IATA.get(destination)
                            if iata:
                                an_aircraft['destination_iata'] = iata
                        fa_flight_id = an_aircraft.get('faFlightID')
                        if fa_flight_id:
                            flight_info = flight_info_extended(fa_flight_id)
                            if flight_info:
                                flight_info_ex_results = flight_info.get('FlightInfoExResult')
                                if flight_info_ex_results and isinstance(flight_info_ex_results, dict):
                                    flights = flight_info_ex_results.get("flights")
                                    if flights and isinstance(flights, list):
                                        an_aircraft['flight_info'] = flights[0]
                    return aircraft

def arrivals(airport_code, number_of_results=15):
    """fetch arrivals - this function is costly"""
    if airport_code:
        icao = AIRPORTS_IATA_TO_ICAO.get(airport_code)
        results = search(destination=icao, number_of_results=number_of_results)
        if results and isinstance(results, dict):
            search_results = results.get('SearchResult')
            if search_results and isinstance(search_results, dict):
                aircraft = search_results.get('aircraft')
                if aircraft and isinstance(aircraft, list):
                    for an_aircraft in aircraft:
                        origin = an_aircraft.get('origin')
                        if origin:
                            iata = AIRPORTS_ICAO_TO_IATA.get(origin)
                            if iata:
                                an_aircraft['origin_iata'] = iata
                        fa_flight_id = an_aircraft.get('faFlightID')
                        if fa_flight_id:
                            flight_info = flight_info_extended(fa_flight_id)
                            if flight_info:
                                flight_info_ex_results = flight_info.get('FlightInfoExResult')
                                if flight_info_ex_results and isinstance(flight_info_ex_results, dict):
                                    flights = flight_info_ex_results.get("flights")
                                    if flights and isinstance(flights, list):
                                        an_aircraft['flight_info'] = flights[0]
                    return aircraft

def arrivals_to_texts(airport_code):
    """print arrivals at an airport"""
    results = arrivals(airport_code)
    response = []
    if not results:
        response.append("did not get any results")
    else:
        results = sorted(results, key=lambda x: x.get('flight_info', {}).get('estimatedarrivaltime'))
        for result in results:
            flight_info = result.get('flight_info')
            if flight_info:
                estimated_arrival_time = flight_info.get('estimatedarrivaltime')
                if estimated_arrival_time:
                    estimated_arrival_time = datetime.datetime.fromtimestamp(estimated_arrival_time)
                response.append("flight {} from {} will arrive at {}".format(flight_info.get("ident"),
                                                                             flight_info.get('originCity'),
                                                                             estimated_arrival_time))
    return response


def departures_to_text(airport_code):
    """print departures at an airport"""
    results = departures(airport_code)
    response = []
    if not results:
        response.append("did not get any results")
    else:

        for res in results:
            flight_info = res.get('flight_info')
            if flight_info:
                departure_time = flight_info.get('actualdeparturetime') or flight_info.get('filed_departuretime')
                if departure_time:
                    res['departure_time'] = datetime.datetime.fromtimestamp(departure_time)
        results = sorted(results, key=lambda x: x.get('departure_time'))
        for result in results:
            flight_info = result.get('flight_info')
            if flight_info:
                response.append("flight {} to {} will depart at {}".format(flight_info.get("ident"),
                                                                           flight_info.get('destinationCity'),
                                                                           result['departure_time']))
    return response

def demo():
    """Play with FlightAware"""
    res = requests.get(URL + "MetarEx?airport=KJFK&startTime=0&howMany=1&offset=0", auth=(USERNAME, API_KEY))
    if res.status_code == requests.codes.ok:  # @UndefinedVariable pylint:disable=no-member
        print(res.json())


def fa_api_airline_flight_schedules(start_date, end_date, origin=None, destination=None, airline=None, flight_number=None,
                                    how_many=None):
    """
    AirlineFlightSchedules returns flight schedules that have been published by airlines.
    These schedules are available for the recent past as well as up to one year into the future.
    Flights performed by airline codeshares are also returned in these results.

    startDate   int    timestamp of earliest flight departure to return, specified in integer seconds since 1970 (UNIX epoch time).
                       Use UTC/GMT to convert the local time at the departure airport to this timestamp.
    endDate     int    timestamp of latest flight departure to return, specified in integer seconds since 1970 (UNIX epoch time).
                       Use UTC/GMT to convert the local time at the departure airport to this timestamp.
    origin      string optional airport code of origin. If blank or unspecified, then flights with any origin will be returned.
    destination string optional airport code of destination. If blank or unspecified, then flights with any destination will be
                       returned.
    airline     string optional airline code of the carrier. If blank or unspecified, then flights on any airline will be returned.
    flightno    string optional flight number. If blank or unspecified, then any flight number will be returned.
    howMany     int    maximum number of past records to obtain. Must be a positive integer value less than or equal to 15,
                       unless SetMaximumResultSize has been called.
    offset      int    must be an integer value of the offset row count you want the search to start at.
                       Most requests should be 0 (most recent report).
    """
    scheduled = []
    not_done = True
    how_many = how_many or 15
    params = dict(startDate=calendar.timegm(start_date.timetuple()),
                  endDate=calendar.timegm(end_date.timetuple()),
                  offset=0)
    if origin:
        params['origin'] = AIRPORTS_IATA_TO_ICAO.get(origin, origin)
    if destination:
        params['destination'] = AIRPORTS_IATA_TO_ICAO.get(destination, destination)
    if airline:
        params['airline'] = airline
    if flight_number:
        params['flightno'] = unicode(flight_number)
    while not_done:
        batch_results = flight_aware("AirlineFlightSchedules", params)
        scheduled_result = batch_results.get("AirlineFlightSchedulesResult")
        if scheduled_result and isinstance(scheduled_result, dict):
            scheduled_batch = scheduled_result.get('data')
            if scheduled_batch and isinstance(scheduled_batch, list):
                scheduled.extend(scheduled_batch)
            if len(scheduled) > how_many:
                break
            next_offset = scheduled_result.get("next_offset")
            print(next_offset, type(next_offset))
            if next_offset and isinstance(next_offset, int) and next_offset != -1:
                params['offset'] = next_offset
                continue
        not_done = False
    # Before we return, let's do some processing on the results:
    for flight in scheduled:
        departure_time = flight.get('departuretime')
        if departure_time:
            flight['departure_time'] = datetime.datetime.fromtimestamp(departure_time)
        arrival_time = flight.get('arrivaltime')
        if arrival_time:
            flight['arrival_time'] = datetime.datetime.fromtimestamp(arrival_time)
    scheduled = sorted(scheduled, key=lambda res: res.get('departuretime'))
    return scheduled

def fa_api_scheduled(airport, how_many, filter_enum="", offset=0, filter_ident=None):
    """
    Scheduled returns information about scheduled flights (technically, filed IFR flights) for a specified airport and a
    maximum number of flights to be returned. Scheduled flights are returned from soonest to furthest in the future to depart.
    Only flights that have not actually departed, and have a scheduled departure time between 2 hours in the past and 24 hours
    in the future, are considered.
    Times returned are seconds since 1970 (UNIX epoch time).
    See also Arrived, Departed, and Enroute for other airport tracking functionality.

    airport   string    the ICAO airport ID (e.g., KLAX, KSFO, KIAH, KHOU, KJFK, KEWR, KORD, KATL, etc.)
    howMany   int       determines the number of results. Must be a positive integer value less than or equal to 15,
                        unless SetMaximumResultSize has been called.
    filter    string    can be "ga" to show only general aviation traffic, "airline" to only show airline traffic, or null/empty
                        to show all traffic.
    offset    int       must be an integer value of the offset row count you want the search to start at. Most requests should be 0.

    filter_ident - Each result has a flight number that looks like this:   'ident': 'QTR579'.
                   Use filter_ident to filter only 'ident's that start with your provided string.
                   Allows for searching for airlines and even specific flights.

    Response Example: [{u'aircrafttype': u'AT72',
                  u'destination': u'VICG',
                  u'destinationCity': u'Chandigarh',
                  u'destinationName': u'Chandigarh (Chandigarh Air Force Base)',
                  u'estimatedarrivaltime': 1467025560,
                  u'filed_departuretime': 1467021600,
                  u'ident': u'JAI2657',
                  u'origin': u'VIDP',
                  u'originCity': u'New Delhi',
                  u'originName': u"Indira Gandhi Int'l"},
                ..]
    """
    scheduled = []
    not_done = True
    params = dict(airport=airport, howMany=how_many, filter=filter_enum, offset=offset)
    while not_done:
        batch_results = flight_aware("Scheduled", params)
        scheduled_result = batch_results.get("ScheduledResult")
        if scheduled_result and isinstance(scheduled_result, dict):
            scheduled_batch = scheduled_result.get('scheduled')
            if scheduled_batch and isinstance(scheduled_batch, list):
                if filter_ident:
                    scheduled_batch = [flight for flight in scheduled_batch if flight.get('ident').startswith(filter_ident)]
                scheduled.extend(scheduled_batch)
            if len(scheduled) > how_many:
                break
            next_offset = scheduled_result.get("next_offset")
            print(next_offset, type(next_offset))
            if next_offset and isinstance(next_offset, int) and next_offset != -1:
                params['offset'] = next_offset
                continue
        not_done = False
    return scheduled

def get_icao_search_query(airports_list):
    """ icao codes or airports for query """
    icao_airport_codes = [AIRPORTS_IATA_TO_ICAO.get(airport) for airport in airports_list]
    icao_airport_codes = [code for code in icao_airport_codes if code]
    airport_codes_str = None
    if icao_airport_codes:
        if len(icao_airport_codes) == 1:
            airport_codes_str = icao_airport_codes[0]
        else:
            airport_codes_str = "{" + " ".join(icao_airport_codes) + "}"
    return airport_codes_str


def search_for_flight_from_to(from_airports, to_airports):
    """Search for a flight from an airport to an airport on a specific date"""
    from_icao = get_icao_search_query(from_airports)
    to_icao = get_icao_search_query(to_airports)
    results = search(destination=to_icao, origin=from_icao, number_of_results=DEFAULT_NUMBER_OF_SEARCH_RESULTS)
    print(results)
    if results and isinstance(results, dict):
        search_results = results.get('SearchResult')
        if search_results and isinstance(search_results, dict):
            aircraft = search_results.get('aircraft')
            if aircraft and isinstance(aircraft, list):
                for an_aircraft in aircraft:
                    pprint(an_aircraft)

def demo_fa_api_scheduled(departure_airport, filter_ident=None):
    """Play with fa_api_scheduled"""
    icao = AIRPORTS_IATA_TO_ICAO.get(departure_airport)
    pprint(fa_api_scheduled(icao, how_many=15, filter_ident=filter_ident))

def fa_api_arrivals(airport, H):
    """
        airport    string    the ICAO airport ID (e.g., KLAX, KSFO, KIAH, KHOU, KJFK, KEWR, KORD, KATL, etc.)
        howMany    int    determines the number of results. Must be a positive integer value less than or equal to 15, unless SetMaximumResultSize has been called.
        filter    string    can be "ga" to show only general aviation traffic, "airline" to only show airline traffic, or null/empty to show all traffic.
        offset    int    must be an integer value of the offset row count you want the search to start at. Most requests should be 0.
    """

def get_flight_status_data(body):
    """ Get data about flight from FlightAware API - and format the output in a FB Flight update format """
    flight_number = '{}{}'.format(body['ICAO'], body['Number'])
    departure_date = body.get('departure', '').split('T')[0]
    if departure_date:
        departure_date = datetime.datetime.strptime(departure_date, "%Y-%m-%d").date()
    else:
        departure_date = None
    arrival_date = body.get('arrival', '').split('T')[0]
    if arrival_date:
        arrival_date = datetime.datetime.strptime(arrival_date, "%Y-%m-%d").date()
    else:
        arrival_date = None

    if not arrival_date and not departure_date:
        next_flight = find_next_flight(flight_number)
        if not isinstance(next_flight, dict):
            return

        faFlightID = next_flight.get('InFlightInfoResult', {}).get('faFlightID')
        if not faFlightID:
            return
    else:
        faFlightID = flight_number


    FlightInfoExResult = flight_info_extended(faFlightID, departure_date=departure_date, arrival_date=arrival_date)

    flights = FlightInfoExResult.get('FlightInfoExResult', {}).get('flights')
    extended_info = flights[0] if flights else None
    if not extended_info:
        return
    
    faFlightID = extended_info.get('faFlightID')
    AirlineFlightInfoResult = flight_airline_info(faFlightID)
    airline_info = AirlineFlightInfoResult.get('AirlineFlightInfoResult', {})
    if not airline_info:
        return

    # origin
    orig_airport_icao_code = extended_info.get('origin')
    orig_airport_code = AIRPORTS_ICAO_TO_IATA.get(orig_airport_icao_code, orig_airport_icao_code)
    if orig_airport_code in FA_AIRPORTS:
        origin_tz = pytz_timezone(FA_AIRPORTS[orig_airport_code]['timezone'].lstrip(':'))
    else:
        origin_tz = None
    filed_departuretime = extended_info['filed_departuretime']
    actual_departuretime = extended_info.get('actualdeparturetime')
    depart_date = datetime.datetime.fromtimestamp(filed_departuretime, origin_tz)
    if actual_departuretime:
        actual_departuretime = datetime.datetime.fromtimestamp(actual_departuretime, origin_tz)

    # destination
    destination_icao_code = extended_info.get('destination')
    dest_airport_code = AIRPORTS_ICAO_TO_IATA.get(destination_icao_code, destination_icao_code)
    if dest_airport_code in FA_AIRPORTS:
        destination_tz = pytz_timezone(FA_AIRPORTS[dest_airport_code]['timezone'].lstrip(':'))
    else:
        destination_tz = None
    estimatedarrivaltime = extended_info['estimatedarrivaltime']
    arrival_date = datetime.datetime.fromtimestamp(estimatedarrivaltime, destination_tz)

    return dict(
        flight_number=flight_number,
        flight_number_only=body['Number'],
        airline_name=body['Name'],
        departure_airport={
            "airport_code": orig_airport_code,
            "city":extended_info['originName'],
            "gate":airline_info['gate_orig'],
            "terminal":airline_info['terminal_orig']
        },
        arrival_airport={
            "airport_code": dest_airport_code,
            "city": extended_info.get('destinationName'),
            "gate": airline_info['gate_dest'],
            "terminal": airline_info['terminal_dest']
        },
        flight_schedule={
            "departure_time": depart_date,
            "departure_time_actual": actual_departuretime,
            "arrival_time": arrival_date,
            "boarding_time": "",
        }
    )

def demo_fa_api_airline_flight_schedules():
    """Demo fa_api_airline_flight_schedules()"""
    start_date = datetime.date(2016, 6, 24)
    end_date = datetime.date(2016, 6, 25)  # ## NOT INCLUDING!
    origin = "JFK"
    destination = "ORD"
    airline = "JBU"
    pprint(fa_api_airline_flight_schedules(start_date, end_date, origin=origin, destination=destination, airline=airline))

if __name__ == '__main__':
    pprint(departures_to_text("TLV"))

#     pprint(find_next_flight("QTR1"))
#     pprint(flight_info_extended("DAL2824-1463808481-airline-0168"))
#     pprint(flight_info_extended("QTR1", departure_date=datetime.date(2016, 6, 14)))
#     pprint(airline_info("QTR"))
#     pprint(flight_info_extended("QTR1", departure_date=datetime.date(2016, 6, 14)))
#     demo_print_departures("TLV")
#     search_for_flight_from_to(["ORD", "MDW"], ["JFK", "EWR", "LGA"])
#     demo_fa_api_scheduled(departure_airport="DEL")
#     demo_fa_api_airline_flight_schedules()
