'''
Created on Jun 29, 2016

@author: evature

 https://developer.flightstats.com/api-docs/scheduledFlights/v1

'''
import os
import requests
import datetime
from pprint import pprint
from pytz import timezone
from flightstats.flightaware_airports import AIRPORTS as FA_AIRPORTS

APPLICATION_ID = os.environ['FLIGHTSTATS_APP_ID']
APPLICATION_KEY = os.environ['FLIGHTSTATS_APP_KEY']


def send_request(search_url):
    req_url = "https://api.flightstats.com/flex/schedules/rest/v1/json/{}?appId={}&appKey={}&codeType=IATA".format(search_url,
                                                                                                                   APPLICATION_ID,
                                                                                                                   APPLICATION_KEY)
    resp = requests.get(req_url)
    if resp.status_code == requests.codes.ok:  # @UndefinedVariable pylint:disable=no-member
        return resp.json()


def arrivals(from_airport, to_airport, arrival_date):
    """
        finds arrivals
        @from_airport The airport code (IATA) of the departure airport (required)
        @to_airport The airport code (IATA) of the arrival airport (required)
        @arrival_date arrival date (required)
    """
    search_url = "from/{from_airport}/to/{to_airport}/arriving/{arrival_year}/{arrival_month}/{arrival_day}".format(from_airport=from_airport,
                                                                                                                    to_airport=to_airport,
                                                                                                                    arrival_year=arrival_date.year,
                                                                                                                    arrival_month=arrival_date.month,
                                                                                                                    arrival_day=arrival_date.day)
    content = send_request(search_url)
    return content

def departures(from_airport, to_airport, departure_date):
    """
        finds departure
        @from_airport The airport code (IATA) of the departure airport (required)
        @to_airport The airport code (IATA) of the arrival airport (required)
        @departure_date departure date (required)
    """
    search_url = "from/{from_airport}/to/{to_airport}/departing/{departure_year}/{departure_month}/{departure_day}".format(from_airport=from_airport,
                                                                                                                    to_airport=to_airport,
                                                                                                                    departure_year=departure_date.year,
                                                                                                                    departure_month=departure_date.month,
                                                                                                                    departure_day=departure_date.day)
    content = send_request(search_url)
    return content

def _helper_results_from_flightstats(response, airline, sort_by_key):
    """ adds flights, airlines and airports """
    response['flights'] = []
    if response and response.get('scheduledFlights'):
        response['flights'] = sorted(response['scheduledFlights'], key=lambda x: x[sort_by_key])
        # removes all code shared flights
        for flight in response['flights'][:]:
            if flight['isCodeshare']:
                response['flights'].remove(flight)

        # filter down by airline
        if airline is not None:
            response['flights'] = [flight for flight in response['flights'] if flight['carrierFsCode'] == airline]

    response['airports'] = {airport['fs']: airport for airport in response['appendix']['airports']}
    response['airlines'] = {airline['fs']: airline for airline in response['appendix']['airlines']}
    return response


def _helper_build_arrival_departure_text(flight_info, airline, airports, airlines, is_arrival):
    if is_arrival:
        date_key = 'arrivalTime'
        location_key = 'departureAirportFsCode'
    else:
        date_key = 'departureTime'
        location_key = 'arrivalAirportFsCode'

    related_datetime = datetime.datetime.strptime(flight_info[date_key], "%Y-%m-%dT%H:%M:%S.%f")
    related_city = airports[flight_info[location_key]]['city']
    resp_text = ''
    main_flight_number = "{}{}".format(flight_info["carrierFsCode"], flight_info["flightNumber"])
    if not flight_info['codeshares'] and airline is None:
        resp_text += airlines[flight_info['carrierFsCode']]['name'] + ' '
    if flight_info['codeshares']:
        code_shared_flights = ["{}{}".format(codeshare["carrierFsCode"], codeshare["flightNumber"]) for codeshare in flight_info['codeshares']]
        resp_text += 'flights {} ({})'.format(main_flight_number, ", ".join(code_shared_flights))
    else:
        resp_text+= "flight {}".format(main_flight_number)
    if is_arrival:
        resp_text += " from {} will arrive at {}".format(related_city, datetime.datetime.strftime(related_datetime, '%H:%M'))
    else:
        resp_text += " to {} will depart at {}".format(related_city, datetime.datetime.strftime(related_datetime, '%H:%M'))
    return resp_text


def arrivals_to_texts(from_airport, to_airport, airline=None, max_results=5):
    """ converts arrivals response from flightstats to list of texts """
    arrival_date = datetime.datetime.now()
    destination_tz = timezone(FA_AIRPORTS[from_airport]['timezone'].lstrip(':'))
    arrival_date = destination_tz.localize(arrival_date)
    content = arrivals(from_airport, to_airport, arrival_date)
    content = _helper_results_from_flightstats(response = content, airline = airline, sort_by_key = 'arrivalTime')
    flights, airports, airlines = content['flights'], content['airports'],  content['airlines']
    if flights:
        responses = []
        for flight_info in flights[:max_results]:
            resp_text = _helper_build_arrival_departure_text(flight_info, airline, airports, airlines, is_arrival = True)
            responses.append(resp_text)
        return responses
    return "did not find any results"

def departures_to_texts(from_airport, to_airport, airline=None, max_results=5):
    """
        converts departures response from flightstats to list of texts
    """
    departure_date = datetime.datetime.now()
    destination_tz = timezone(FA_AIRPORTS[from_airport]['timezone'].lstrip(':'))
    departure_date = destination_tz.localize(departure_date)
    content = departures(from_airport, to_airport, departure_date)
    content = _helper_results_from_flightstats(response = content, airline = airline, sort_by_key = 'departureTime')
    flights, airports, airlines = content['flights'], content['airports'],  content['airlines']
    if flights:
        responses = []
        for flight_info in flights[:max_results]:
            resp_text = _helper_build_arrival_departure_text(flight_info, airline, airports, airlines, is_arrival = False)
            responses.append(resp_text)
        return responses
    return "did not find any results"

def demo_departures():
    from_airport = "ORD"
    to_airport = "JFK"
    pprint(departures_to_texts(from_airport, to_airport))

def demo_arrivals():
    from_airport = "ORD"
    to_airport = "JFK"
    pprint(arrivals_to_texts(from_airport, to_airport, airline="B6"))


if __name__ == '__main__':
    demo_departures()
