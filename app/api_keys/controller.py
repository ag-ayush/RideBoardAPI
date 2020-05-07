from flask import Blueprint, jsonify, abort
from flask_cors import cross_origin
from app import db
from app.auth.controller import get_current_user
from app.utils import model_list_to_dict_list, get_value_from_payload
from app.models_schema import APIKeySchema
from app.models_db import APIKey


api_keys = Blueprint('api_keys', __name__, url_prefix='/keys/')
key_schema = APIKeySchema()


@api_keys.route('', methods=['POST'])
@get_current_user(True)
def generate_api_key(current_user):
    if current_user is None:
        abort(403, "You are not authorized to see this.")

    reason = get_value_from_payload("reason")
    if check_key_unique(current_user.id, reason):
        abort(400, "There's already a key with this reason for this user!")

    # Creates the new API key
    new_key = APIKey(current_user.id, reason)
    # Adds, flushes and commits the new object to the database
    db.session.add(new_key)
    db.session.flush()
    db.session.commit()
    return jsonify(key_schema.dump(new_key))


@api_keys.route('', methods=['GET'])
@cross_origin(headers=['Content-Type'])
@get_current_user(True)
def list_api_keys(current_user):
    if current_user is None:
        abort(403, "You are not authorized to see this.")
    return jsonify(model_list_to_dict_list(APIKey.query.all(), key_schema))


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
