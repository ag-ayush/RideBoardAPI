from flask import (Blueprint, jsonify)
from app import db, models
from app.auth.controller import requires_token


home = Blueprint('home', __name__, url_prefix='/home')


@home.route('/unprotected', methods = ['GET'])
def home_route_unprotected():
	title = "Homepage"
	data = "Hello, World!"
	return jsonify({'title': title, 'data': data})


@home.route('/protected', methods = ['GET'])
@requires_token
def home_route_protected(current_user):
	title = "Homepage"
	data = "Hello, World!"
	return jsonify({'title': title, 'data': data, 'current_user': current_user.id})