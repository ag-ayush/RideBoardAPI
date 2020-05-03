

from flask import (Blueprint, request, redirect, url_for, jsonify)

from app import db
from app.auth.controller import requires_token
from app.utils import list_model_to_json_list
from app.models import Team, UserTeam

from app.models import Event, Rider, Car, User

teams = Blueprint('team', __name__, url_prefix='/teams')


@teams.route('/all', methods=['GET'])
@requires_token
def get_teams(current_user):
    team_ids = db.session.query(UserTeam.team_id).filter_by(
        user_id=current_user.id).all()
    teams = list(map(db.session.query(Team).get, team_ids))

    json_build = {"teams": list_model_to_json_list(teams)}
    return jsonify(json_build)
