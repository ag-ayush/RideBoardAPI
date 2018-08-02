####################################
# File name: __init__.py           #
# Author: Ayush Goel               #
####################################
import json
import os
import markdown
from flask import Flask, request, jsonify, session, redirect, Markup
from flask_cors import cross_origin
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

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
from rideboard_api.models import Ride, Rider, Car


@app.route('/', methods=['GET'])
@app.template_filter("markdown")
def index():
    f = open('README.md', 'r')
    return markdown.markdown(f.read(), extensions=['markdown.extensions.tables', 'markdown.extensions.fenced_code'])


@app.route('/all', methods=['GET'])
@cross_origin(headers=['Content-Type'])
def all_events():
    """
    Returns all Events in the database
    :return: Returns JSON of all quotes in the rideboard database
    """
    rideid = request.args.get('id')
    query = []
    if rideid is not None:
        # adds a Ride object to the List:query
        query.append(Ride.query.get(rideid))
    else:
        # Makes query a List of all rides
        query = Ride.query.all()
    return parse_event_as_json(query)


@app.route('/upcoming', methods=['GET'])
@cross_origin(headers=['Content-Type'])
def upcoming_event():
    """
    Returns the Event with the earliest start_time as JSON
    :return: JSON of the upcoming event
    """
    query = Ride.query.order_by(Ride.start_time.asc()).first()
    return jsonify(return_event_json(query))


@app.route('/join/<car_id>/<username>/<first_name>/<last_name>/', methods=['GET'])
@cross_origin(headers=['Content-Type'])
def join_car(car_id, username: str, first_name: str, last_name: str):
    """
    Adds username to the Car and returns the Event as JSON
    :param car_id: ID of the car to add the username to
    :param username: username
    :param first_name: First name of the user [from CSH LDAP given username]
    :param last_name: Last name of the user [from CSH LDAP given username]
    :return: Event as JSON in which the Car belongs or 400 in case of error.
    """
    # TODO: This method only works with GET, but I believe this should be a POST.
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
    else:
        return "You already joined a ride, or are the owner of one!", 400


# TODO: rideform, carform, delete ride, delete car, leave ride, api-key


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
