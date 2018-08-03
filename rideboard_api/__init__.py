#########################################
# File name: __init__.py                #
# Author: Ayush Goel                    #
#                                       #
# Credits to Devin for providing        #
# functions for generating and checking #
# API keys.                             #
#########################################
import os
import markdown
from flask import Flask, request, jsonify, redirect
from flask_cors import cross_origin
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_sqlalchemy import SQLAlchemy

# Setting up Flask
app = Flask(__name__)

# Get app config from absolute file path
if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

db = SQLAlchemy(app)

# OIDC Authentication, for CSH member login.
auth = OIDCAuthentication(app, issuer=app.config["OIDC_ISSUER"],
                          client_registration_info=app.config["OIDC_CLIENT_CONFIG"])

# pylint: disable=wrong-import-position
from rideboard_api.models import Ride, Rider, Car, APIKey
from .utils import user_auth


@app.route('/', methods=['GET'])
@app.template_filter("markdown")
def index():
    f = open('README.md', 'r')
    return markdown.markdown(f.read(), extensions=['markdown.extensions.tables', 'markdown.extensions.fenced_code'])


@app.route('/<api_key>/all', methods=['GET'])
@cross_origin(headers=['Content-Type'])
def all_events(api_key: str):
    """
    Returns all Events in the database
    :param api_key: API key allowing for the use of the API
    :return: Returns JSON of all quotes in the rideboard database
    """
    if check_key(api_key):
        rideid = request.args.get('id')
        query = []
        if rideid is not None:
            # adds a Ride object to the List:query
            query.append(Ride.query.get(rideid))
        else:
            # Makes query a List of all rides
            query = Ride.query.all()
        return parse_event_as_json(query)
    return "Invalid API Key!", 403


@app.route('/<api_key>/upcoming', methods=['GET'])
@cross_origin(headers=['Content-Type'])
def upcoming_event(api_key: str):
    """
    Returns the Event with the earliest start_time as JSON
    :param api_key: API key allowing for the use of the API
    :return: JSON of the upcoming event
    """
    if check_key(api_key):
        query = Ride.query.order_by(Ride.start_time.asc()).first()
        return jsonify(return_event_json(query))
    return "Invalid API Key!", 403


@app.route('/<api_key>/join/<car_id>/<username>/<first_name>/<last_name>/', methods=['GET'])
@cross_origin(headers=['Content-Type'])
def join_car(car_id, username: str, first_name: str, last_name: str, api_key: str):
    """
    Adds username to the Car and returns the Event as JSON
    :param car_id: ID of the car to add the username to
    :param username: username
    :param first_name: First name of the user [from CSH LDAP given username]
    :param last_name: Last name of the user [from CSH LDAP given username]
    :param api_key: API key allowing for the use of the API
    :return: Event as JSON in which the Car belongs or 400 in case of error.
    """
    # TODO: This method only works with GET, but I believe this should be a POST.
    if check_key(api_key):
        incar = False
        name = first_name+" "+last_name
        car = Car.query.filter(Car.id == car_id).first()
        event = Ride.query.filter(Ride.id == car.ride_id).first()
        for c in event.cars:
            if c.username == username:
                incar = True
            for person in c.riders:
                if person.username == username:
                    incar = True
        if (car.current_capacity < car.max_capacity or car.max_capacity == 0) and not incar:
            rider = Rider(username, name, car_id)
            car.current_capacity += 1
            db.session.add(rider)
            db.session.add(car)
            db.session.commit()
            return jsonify(return_event_json(event))
        return "The car is either full, or you have already joined a ride, or you are the owner of one!", 400
    return "Invalid API Key!", 403


@app.route('/<api_key>/leave/<car_id>/<username>/', methods=['GET'])
@cross_origin(headers=['Content-Type'])
def leave_ride(car_id, username: str, api_key: str):
    """
    Removes username from the Car and returns the associated Event as JSON
    :param car_id: ID of the car to remove the username from
    :param username: username
    :param api_key: API key allowing for the use of the API
    :return: Event as JSON in which the Car belongs to.
    """
    # TODO: Should be a POST; may be use /leave/event_id/username instead or allow both using params instead of route.
    if check_key(api_key):
        car = Car.query.filter(Car.id == car_id).first()
        rider = Rider.query.filter(Rider.username == username, Rider.car_id == car_id).first()
        event = Ride.query.filter(Ride.id == car.ride_id).first()
        if rider is not None:
            db.session.delete(rider)
            car.current_capacity -= 1
            db.session.add(car)
            db.session.commit()
            return jsonify(return_event_json(event))
        return "You do not exist in that car!", 400
    return "Invalid API Key!", 403


@app.route('/generatekey/<reason>')
@auth.oidc_auth
@user_auth
def generate_api_key(reason: str, metadata=None):
    """
    Creates an API key for the user requested.
    Using a reason and the username grabbed through the @auth.oidc_auth call
    :param reason: Reason for the API key
    :param metadata: auth dictionary
    :return: Hash of the Key or a String stating an error
    """
    if not check_key_unique(metadata['uid'], reason):
        # Creates the new API key
        new_key = APIKey(metadata['uid'], reason)
        # Adds, flushes and commits the new object to the database
        db.session.add(new_key)
        db.session.flush()
        db.session.commit()
        return new_key.hash
    return "There's already a key with this reason for this user!"


# TODO: rideform, carform, delete ride, delete car


def check_key(api_key: str) -> bool:
    """
    Checks if the key exists.
    :param api_key: API key
    :return: true if the key exists in the databse
    """
    keys = APIKey.query.filter_by(hash=api_key).all()
    if keys:
        return True
    return False


def check_key_unique(owner: str, reason: str) -> bool:
    """
    Checks if there is an unique key of a given user and reason
    :param owner: generator of the key
    :param reason: reason provided for the key
    :return: true if the key exists uniquely
    """
    keys = APIKey.query.filter_by(owner=owner, reason=reason).all()
    if keys:
        return True
    return False


def return_event_json(event: Ride):
    """
    Returns an Event Object as JSON
    :param event: The event object being formatted
    :return: Returns a dictionary of the event object formatted to return as JSON
    """
    open_seats = 0
    if event.cars is not None:
        for car in event.cars:
            open_seats += car.max_capacity - car.current_capacity
    return {
        'id': event.id,
        'name': event.name,
        'address': event.address,
        'start_time': event.start_time,
        'end_time': event.end_time,
        'creator': event.creator,
        'open_seats': open_seats,
        'cars': parse_car_as_dict(event.cars)
    }


def parse_event_as_json(events: list, event_json=None) -> list:
    """
    Builds a list of Events as JSON
    :param events: List of Event Objects
    :param event_json: List of Event Objects as dicts
    :return: Returns a list of Event Objects as dicts
    """
    if event_json is None:
        event_json = []
    for event in events:
        event_json.append(return_event_json(event))
    return jsonify(event_json)


def return_car_dict(car: Car):
    """
    Returns a Car Object as dictionary
    :param car: The car object being formatted
    :return: Returns a dictionary of the car object formatted to return as dictionary
    """
    riders = []
    for rider in car.riders:
        riders.append(rider.username)
    return {
        'id': car.id,
        'name': car.name,
        'username': car.username,
        'current_capacity': car.current_capacity,
        'max_capacity': car.max_capacity,
        'departure_time': car.departure_time,
        'return_time': car.return_time,
        'driver_comment': car.driver_comment,
        'ride_id': car.ride_id,
        'riders': riders,
    }


def parse_car_as_dict(cars: list, car_dict=None) -> list:
    """
    Builds a list of Cars as JSON
    :param cars: List of Car Objects
    :param car_dict: List of Car Objects as dicts
    :return: Returns a list of Car Objects as dicts
    """
    if car_dict is None:
        car_dict = []
    for event in cars:
        car_dict.append(return_car_dict(event))
    return car_dict


@app.route("/logout")
@auth.oidc_logout
def _logout():
    return redirect("/", 302)
