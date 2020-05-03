def parse_payload_csh(payload):
	uid = str(payload.get("preferred_username", ""))
	last = str(payload.get("family_name", ""))
	first = str(payload.get("given_name", ""))
	picture = "https://profiles.csh.rit.edu/image/" + uid
	auth_dict = {
		"first": first,
		"last": last,
		"uid": uid,
		"picture": picture
	}
	return auth_dict


def parse_payload_google(payload):
	uid = str(payload.get("sub", ""))
	last = str(payload.get("family_name", ""))
	first = str(payload.get("given_name", ""))
	picture = str(payload.get("picture", ""))
	auth_dict = {
		"first": first,
		"last": last,
		"uid": uid,
		"picture": picture
	}
	return auth_dict