import datetime
import pytz

from app import db
from app.auth.controller import requires_token
from app.utils import list_model_to_json_list

from app.models import Event, Rider, Car, User

events = Blueprint('events', __name__, url_prefix='/events')

# TODO: constants
eastern = pytz.timezone('US/Eastern')
fmt = '%Y-%m-%d %H:%M'

@events.route('/all')
@requires_token
def events(current_user):
    # TODO: Check user in team
    teamid = request.form.get("team_id") if request.form.get("team_id") is not None else return jsonify({'message' : 'Missing team_id.'}), 400

    team = Team.query.filter_by(id=teamid).first()

    # Get all the events and current EST time.
    events = Event.query.filter_by(team_id=teamid).all()
    loc_dt = datetime.datetime.now(tz=eastern)
    st = loc_dt.strftime(fmt)

    rider_instance = []
    if current_user.is_authenticated:
        # TODO: Likely don't need this for loop, should be a single query.
        for rider_instances in Rider.query.filter(Rider.username == current_user.id).all():
            rider_instance.append(Car.query.get(
                rider_instances.car_id).event_id)
        for rider_instances in Car.query.all():
            if rider_instances.username == current_user.id:
                rider_instance.append(rider_instances.event_id)

    # If any event has expired by 1 hour then expire the event.
    for event in events:
        t = datetime.datetime.strftime(
            (event.end_time + datetime.timedelta(hours=1)), '%Y-%m-%d %H:%M')
        if st > t:
            event.expired = True
            db.session.commit()

    # Query one more time for the display.
    events = Event.query.filter_by(team_id=teamid, expired=False).order_by(
        Event.start_time.asc()).all()  # pylint: disable=singleton-comparison

    json_build = {"events": []}
    for event in events:
        json_build["events"].append(to_json(event))
    return jsonify(json_build)