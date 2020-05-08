import datetime
import pytz

from itertools import chain
from sqlalchemy.orm import subqueryload
from flask import Blueprint, jsonify, request, Response, abort

from app import db
from app.auth.controller import get_current_user
from app.utils import model_list_to_dict_list, get_value_from_payload, user_in_team, user_is_event_creator, check_key
from app.models_db import Event, Passenger, Car, User, Team
from app.models_schema import EventSchema, PassengerSchema, CarSchema, UserSchema, TeamSchema

cars = Blueprint('cars', __name__,
                 url_prefix='/teams/<team_id>/events/<event_id>/cars/')
car_schema = CarSchema(exclude=("passengers",))
car_schema_nested = CarSchema()


@cars.route('/', methods=['GET'])
@check_key
@user_in_team
def get_all_cars(team_id, event_id):
    event_schema = EventSchema(only=("cars",))
    event_obj = Event.query.get(event_id)
    json_out = event_schema.dump(event_obj)
    return jsonify(json_out)


@cars.route('/', methods=['POST'])
@check_key
@user_in_team
@get_current_user()
def create_car(team_id, event_id, current_user):
    # TODO: get car by username, and check all passengers??? if none create, else abort
    username = current_user.id
    name = get_value_from_payload("name")
    current_capacity = 0
    max_capacity = get_value_from_payload("max_capacity")
    departure_time = get_value_from_payload("departure_time")
    return_time = get_value_from_payload("return_time")
    driver_comment = get_value_from_payload("driver_comment")
    car = Car(username, name, current_capacity, max_capacity,
              departure_time, return_time, driver_comment, event_id)
    db.session.add(car)
    db.session.commit()
    return Response(status=201)


@cars.route('/<car_id>', methods=['GET'])
@check_key
@user_in_team
def get_car(team_id, event_id, car_id):
    car = Car.query.get(car_id)
    if car is None:
        abort(404, "Car not found")
    json_build = model_list_to_dict_list([car], car_schema_nested)
    return jsonify(json_build[0])


@cars.route('/<car_id>', methods=['PATCH'])
@user_in_team
@user_is_event_creator
def update_event(team_id, event_id, car_id):
    car = Car.query.get(car_id)

    if car is None:
        abort(404, "Car not found")

    name = get_value_from_payload("name", optional=True)
    max_capacity = get_value_from_payload("address", optional=True)
    departure_time = get_value_from_payload("departure_time", optional=True)
    return_time = get_value_from_payload("return_time", optional=True)
    driver_comment = get_value_from_payload("driver_comment", optional=True)

    if name is not None:
        car.name = name
    if max_capacity is not None:
        # TODO: move people if lower
        car.max_capacity = max_capacity
    if departure_time is not None:
        car.departure_time = departure_time
    if return_time is not None:
        car.return_time = return_time
    if driver_comment is not None:
        car.driver_comment = driver_comment

    db.session.commit()
    return Response(status=200)


@cars.route('/<car_id>', methods=["DELETE"])
@check_key
# TODO: this method @user_is_car_owner
def delete_team(team_id):
    team = Team.query.get(team_id)
    if team is None:
        abort(404, "Team not found")
    db.session.delete(team)
    db.session.commit()
    return Response(status=204)


# TODO: Join car
# @app.route('/join/<string:car_id>/<user>', methods=["GET"])
# @login_required
# def join_car(car_id, user):
#     incar = False
#     username = current_user.id
#     name = current_user.firstname + " " + current_user.lastname
#     car = Car.query.get(car_id)
#     event = Event.query.get(car.event_id)
#     attempted_username = user
#     if attempted_username == username:
#         for c in event.cars:
#             if c.username == username:
#                 incar = True
#             for person in c.passengers:
#                 if person.username == username:
#                     incar = True
#         if (car.current_capacity < car.max_capacity or car.max_capacity == 0) and not incar:
#             passenger = Passenger(username, name, car_id)
#             car.current_capacity += 1
#             db.session.add(passenger)
#             db.session.add(car)
#             db.session.commit()
#     return redirect(url_for('events', teamid=event.team_id))

# TODO: Leave car
# @app.route('/delete/passenger/<string:car_id>/<string:passenger_username>', methods=["GET"])
# @login_required
# def leave_car(car_id, passenger_username):
#     username = current_user.id
#     car = Car.query.get(car_id)
#     event = Event.query.get(car.event_id)
#     passenger = Passenger.query.filter(Passenger.username == passenger_username, Passenger.car_id == car_id).first()
#     if passenger.username == username and passenger is not None:
#         db.session.delete(passenger)
#         car.current_capacity -= 1
#         db.session.add(car)
#         db.session.commit()
#     return redirect(url_for('events', teamid=event.team_id))