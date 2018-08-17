#########################################
# File name: __init__.py                #
# Author: Ayush Goel                    #
#                                       #
# Credits to Devin for providing        #
# functions for generating and checking #
# API keys.                             #
#########################################
import os
from datetime import datetime
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
    :return: Returns JSON of all events in the rideboard database
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
        return parse_events_as_json(query)
    return "Invalid API Key!", 403

@app.route('/<api_key>/get/car', methods=['GET'])
@cross_origin(headers=['Content-Type'])
def all_cars(api_key: str):
    """
    Returns all Cars in the database
    :param api_key: API key allowing for the use of the API
    :return: Returns JSON of all cars in the rideboard database
    """
    if check_key(api_key):
        carid = request.args.get('id')
        query = []
        if carid is not None:
            # adds a Car object to the List:query
            query.append(Car.query.get(carid))
        else:
            # Makes query a List of all cars
            query = Car.query.all()
        return parse_cars_as_json(query)
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


@app.route('/<api_key>/join/<car_id>/<username>/<first_name>/<last_name>', methods=['PUT'])
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
    # TODO: Don't use the car_id, use event_id and car owner's uid
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


@app.route('/<api_key>/leave/<event_id>/<username>', methods=['PUT'])
@cross_origin(headers=['Content-Type'])
def leave_ride(event_id, username: str, api_key: str):
    """
    Removes username from the Car and returns the associated Event as JSON
    :param event_id: ID of the car to remove the username from
    :param username: username
    :param api_key: API key allowing for the use of the API
    :return: Event as JSON in which the Car belongs to.
    """
    if check_key(api_key):
        event = Ride.query.filter(Ride.id == event_id).first()
        for car in event.cars:
            rider = Rider.query.filter(Rider.username == username, Rider.car_id == car.id).first()
            if rider is not None:
                db.session.delete(rider)
                car.current_capacity -= 1
                db.session.add(car)
                db.session.commit()
                return jsonify(return_event_json(event))
        return "You are not a rider in that event!", 400
    return "Invalid API Key!", 403


# TODO: The ifs execute in order. if multiple things were not provided then it would only show the error on the first.
@app.route('/<api_key>/create/event', methods=['POST'])
@cross_origin(headers=['Content-Type'])
def create_event(api_key: str):
    """
    Creates an event from a JSON object.
    :param api_key: API key allowing for the use of the API
    :return: Event as JSON if successful
    """
    if check_key(api_key):
        data = request.get_json()
        if 'name' in data:
            name = data['name']
        else:
            return "Event name not provided!", 400
        if 'address' in data:
            address = data['address']
        else:
            return "Event address not provided!", 400
        if 'start_time' in data:
            start_time = data['start_time']
        else:
            return "Event start_time not provided!", 400
        if 'end_time' in data:
            end_time = data['end_time']
        else:
            return "Event end_time not provided!", 400
        if 'creator' in data:
            creator = data['creator']
        else:
            return "Event creator not provided!", 400
        time_format = '%a, %d %b %Y %H:%M:%S'
        start_time = datetime.strptime(start_time, time_format)
        end_time = datetime.strptime(end_time, time_format)
        ride = Ride(name, address, start_time, end_time, creator)
        db.session.add(ride)
        db.session.commit()
        infinity = Car('∞', 'Need a Ride', 0, 0, start_time, end_time, "", ride.id)
        db.session.add(infinity)
        db.session.commit()
        return jsonify(return_event_json(ride))
    return "Invalid API Key!", 403


# TODO: The ifs execute in order. if multiple things were not provided then it would only show the error on the first.
@app.route('/<api_key>/create/car/<event_id>', methods=['POST'])
@cross_origin(headers=['Content-Type'])
def create_car(api_key: str, event_id):
    """
    Creates a car from a JSON object.
    :param api_key: API key allowing for the use of the API
    :return: Car as JSON if successful
    """
    if check_key(api_key):
        data = request.get_json()
        if 'name' in data:
            name = data['name']
        else:
            return "Car creator's name not provided!", 400
        if 'username' in data:
            username = data['username']
        else:
            return "Car creator's username not provided!", 400
        if 'departure_time' in data:
            departure_time = data['departure_time']
        else:
            return "Car's departure_time not provided!", 400
        if 'return_time' in data:
            return_time = data['return_time']
        else:
            return "Car's return_time not provided!", 400
        if 'max_capacity' in data:
            max_capacity = data['max_capacity']
        else:
            return "Car max_capacity not provided!", 400
        if 'driver_comment' in data:
            driver_comment = data['driver_comment']
        else:
            driver_comment = "No comments provided."
        time_format = '%a, %d %b %Y %H:%M:%S'
        departure_time = datetime.strptime(departure_time, time_format)
        return_time = datetime.strptime(return_time, time_format)
        car = Car(username, name, 0, max_capacity, departure_time, return_time, driver_comment, event_id)
        db.session.add(car)
        db.session.commit()
        return jsonify(return_event_json(Ride.query.filter(Ride.id == event_id).first()))
    return "Invalid API Key!", 403


@app.route('/<api_key>/delete/event/<event_id>/<uid>', methods=['DELETE'])
@cross_origin(headers=['Content-Type'])
def delete_event(api_key: str, event_id, uid):
    """
    Delete an event.
    :param api_key: API key allowing for the use of the API
    :param event_id: ID of the event to delete.
    :param uid: username of the person requesting this.
    :return: Varying status code with message depending on outcome.
    """
    if check_key(api_key):
        event = Ride.query.filter(Ride.id == event_id).first()
        if event is not None:
            if event.creator == uid:
                for car in event.cars:
                    for peeps in car.riders:
                        db.session.delete(peeps)
                    db.session.delete(car)
                db.session.delete(event)
                db.session.commit()
                return "Deletion Successful", 200
            return "You didn't create that event...", 403
        return "That event doesn't exist, check your event_id...", 400
    return "Invalid API Key!", 403


@app.route('/<api_key>/delete/car/<event_id>/<uid>', methods=['DELETE'])
@cross_origin(headers=['Content-Type'])
def delete_car(api_key: str, event_id, uid):
    """
    Delete a car.
    :param api_key: API key allowing for the use of the API
    :param event_id: Id of the car to delete.
    :param uid: username of the person requesting this.
    :return: Varying status code with message depending on outcome.
    """
    if check_key(api_key):
        car = Car.query.filter(Car.username == uid, Car.ride_id == event_id).first()
        if car is not None:
            if car.username == uid:
                for peeps in car.riders:
                    db.session.delete(peeps)
                db.session.delete(car)
                db.session.commit()
                return "Deletion Successful", 200
            return "You don't own that car.", 403
        return "You do not have a car in that event!", 400
    return "Invalid API Key!", 403


@app.route('/generatekey/<reason>', methods=['GET'])
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
        if metadata['is_rtp'] or metadata['uid'] == 'agoel':
            # Creates the new API key
            new_key = APIKey(metadata['uid'], reason)
            # Adds, flushes and commits the new object to the database
            db.session.add(new_key)
            db.session.flush()
            db.session.commit()
            return new_key.hash
        return "You are not authorized to see this.", 403
    return "There's already a key with this reason for this user!", 400


@app.route('/listapikeys', methods=['GET'])
@auth.oidc_auth
@user_auth
@cross_origin(headers=['Content-Type'])
def list_api_keys(metadata=None):
    if metadata['is_rtp'] or metadata['uid'] == 'agoel':
        return parse_apikeys_as_json(APIKey.query.all())
    return "You are not authorized to see this.", 403


def check_key(api_key: str) -> bool:
    """
    Checks if the key exists using the hash
    :param api_key: API key
    :return: true if the key exists in the database
    """
    keys = APIKey.query.filter_by(hash=api_key).all()
    if keys:
        return True
    return False


def check_key_unique(owner: str, reason: str) -> bool:
    """
    Checks if the key exists using the owner and the reason
    :param owner: generator of the key
    :param reason: reason provided for the key
    :return: true if the key exists uniquely
    """
    keys = APIKey.query.filter_by(owner=owner, reason=reason).all()
    if keys:
        return True
    return False


def return_apikey_json(key: APIKey):
    """
    Returns an APIKey Object as JSON
    :param key: The APIKey object being formatted
    :return: Returns the APIKey object formatted to return as JSON
    """
    return {
        'id': key.id,
        'owner': key.owner,
        'hash': key.hash,
        'reason': key.reason
    }


def parse_apikeys_as_json(keys: list, key_json=None) -> list:
    """
    Builds a list of APIKey as JSON
    :param keys: List of APIKey Objects
    :param key_json: List of APIKey Objects as dicts
    :return: Returns a list of APIKey Objects as dicts
    """
    if key_json is None:
        key_json = []
    for key in keys:
        key_json.append(return_apikey_json(key))
    return jsonify(key_json)


def return_event_json(event: Ride):
    """
    Returns an Event Object as JSON
    :param event: The event object being formatted
    :return: Returns the event object formatted to return as JSON
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
        'cars': parse_cars_as_dict(event.cars)
    }


def parse_events_as_json(events: list, event_json=None) -> list:
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
    :return: Returns the car object formatted to return as dictionary
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


def parse_cars_as_dict(cars: list, car_dict=None) -> list:
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


def parse_cars_as_json(cars: list, car_json=None) -> list:
    """
    Builds a list of Cars as JSON
    :param cars: List of Car Objects
    :param car_json: List of Car Objects as dicts
    :return: Returns a list of Car Objects as dicts
    """
    if car_json is None:
        car_json = []
    for car in cars:
        car_json.append(return_car_dict(car))
    return jsonify(car_json)


@app.route("/logout")
@auth.oidc_logout
def _logout():
    return redirect("/", 302)
