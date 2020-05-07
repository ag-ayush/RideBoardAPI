#!/bin/bash

source config.sh
FLASK_APP=run.py FLASK_DEBUG=1 python3 -m flask run --host=$IP --port=$PORT --cert=adhoc
