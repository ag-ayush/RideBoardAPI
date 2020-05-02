import jwt
import json
from functools import wraps
from requests import get
from expiringdict import ExpiringDict

from flask import request, jsonify

GOOGLE_OAUTH2_CERTS_URL="https://www.googleapis.com/oauth2/v3/certs"
CSH_OAUTH2_CERTS_URL="https://sso.csh.rit.edu/auth/realms/csh/protocol/openid-connect/certs"
CERT_URLS_WITH_X5C = [GOOGLE_OAUTH2_CERTS_URL, CSH_OAUTH2_CERTS_URL]
CACHED_KEYS = ExpiringDict(max_len=100, max_age_seconds=3600)
CACHED_LEN = 0


def requires_token(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		global CACHED_KEYS, CACHED_LEN

		token = request.args.get('token')	# TODO: change from https://127.0.0.1:500/route?token=lASUhflahu983ur92u to pass in json
		
		if not token:
			return jsonify(success=False, message="Token is missing."), 403
		try:
			if len(CACHED_KEYS) == 0 or len(CACHED_KEYS) < CACHED_LEN:
				print("Caching latest public keys.")
				items = public_keys()
				CACHED_LEN = len(items)
				CACHED_KEYS = ExpiringDict(max_len=100, max_age_seconds=10, items=items)
			kid = jwt.get_unverified_header(token)['kid']
			key = CACHED_KEYS[kid]
			payload = jwt.decode(token, key=key, algorithms=['RS256'], options={"verify_aud": False})

			# TODO: If google verify audience. Based on Google/CSH, parse the payload and add the auth_dict ti kwargs
		except Exception as e:
			import traceback
			traceback.print_exc()
			return jsonify(success=False, message="Token is invalid.", text=str(e)), 403
		return f(*args, **kwargs)
	return decorated


def public_keys():
	keys = dict()
	
	for cert_url in CERT_URLS_WITH_X5C:
		output_json = get(cert_url).json()
		for k in output_json["keys"]:
			kid = k["kid"]
			public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k))
			keys[kid] = public_key
	
	return keys