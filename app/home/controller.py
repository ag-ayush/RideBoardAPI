from flask import (Blueprint, request, render_template,
                  flash, g, session, redirect, url_for, jsonify)
from app import db, models
from app.auth.controller import requires_token
import app.home.helper as helper


home = Blueprint('home', __name__, url_prefix='/home')


@home.route('/', methods = ['GET'])
@requires_token
def home_route():
	title = "Homepage"
	data = "Hello, World!"
	return jsonify({'title': title, 'data': data})