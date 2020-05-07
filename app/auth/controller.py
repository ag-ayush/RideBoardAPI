import json
from functools import wraps

import jwt
from jwt.exceptions import PyJWTError
from requests import get

from expiringdict import ExpiringDict
from flask import jsonify, request, abort

from app import db
from app.auth.payload_parsers import parse_payload_csh, parse_payload_google
from app.models_db import User

GOOGLE_OAUTH2_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
CSH_OAUTH2_CERTS_URL = "https://sso.csh.rit.edu/auth/realms/csh/protocol/openid-connect/certs"
CERT_URLS_WITH_X5C = [GOOGLE_OAUTH2_CERTS_URL, CSH_OAUTH2_CERTS_URL]
CACHED_KEYS = ExpiringDict(max_len=100, max_age_seconds=3600)
CACHED_LEN = 0


def get_current_user(check_auth_for_key=False):
    def real_get_current_user(f):
        @wraps(f)
        def decorated_get_current_user(*args, **kwargs):
            global CACHED_KEYS, CACHED_LEN

            token = request.headers.get('Authorization').split(" ")[1]

            if not token:
                return jsonify({'message': 'Token is missing!'}), 401
            try:
                if len(CACHED_KEYS) == 0 or len(CACHED_KEYS) < CACHED_LEN:
                    print("Caching latest public keys.")
                    items = public_keys()
                    CACHED_LEN = len(items)
                    CACHED_KEYS = ExpiringDict(
                        max_len=100, max_age_seconds=3600, items=items)
                kid = jwt.get_unverified_header(token)['kid']

                key = CACHED_KEYS[kid][1]
                service = CACHED_KEYS[kid][0]
                payload = jwt.decode(token, key=key, algorithms=[
                                    'RS256'], options={"verify_aud": False})
                auth_dict = dict()
                if service == "google":
                    auth_dict = parse_payload_google(payload)
                elif service == "csh":
                    auth_dict = parse_payload_csh(payload)

                if auth_dict is None:
                    abort(401, 'Could not parse user info properly.')

                if check_auth_for_key and not auth_dict['is_rtp'] and auth_dict["uid"] != 'agoel':
                        kwargs["current_user"] = None
                        return f(*args, **kwargs)

                q = User.query.get(auth_dict['uid'])
                if q is not None:
                    q.firstname = auth_dict['first']
                    q.lastname = auth_dict['last']
                    q.picture = auth_dict['picture']
                else:
                    user = User(auth_dict['uid'], auth_dict['first'],
                                auth_dict['last'], auth_dict['picture'])
                    db.session.add(user)

                db.session.commit()
                kwargs["current_user"] = q
                return f(*args, **kwargs)
            except PyJWTError as e:
                print(e)
                abort(401, 'Token is invalid!')
        return decorated_get_current_user
    return real_get_current_user


def public_keys():
    keys = dict()

    for cert_url in CERT_URLS_WITH_X5C:
        output_json = get(cert_url).json()
        for k in output_json["keys"]:
            kid = k["kid"]
            service = "google" if "googleapis.com" in cert_url else "csh"
            public_key = (
                service, jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k)))
            keys[kid] = public_key

    return keys
