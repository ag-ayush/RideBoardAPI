def parse_payload_csh(payload):
    uid = str(payload.get("preferred_username", ""))
    last = str(payload.get("family_name", ""))
    first = str(payload.get("given_name", ""))
    picture = "https://profiles.csh.rit.edu/image/" + uid
    print(payload.get("groups"))
    is_rtp = 'rtp' in payload.get("groups")
    auth_dict = {
        "first": first,
        "last": last,
        "uid": uid,
        "picture": picture,
        "is_rtp": is_rtp
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
        "picture": picture,
        "is_rtp": False
    }
    return auth_dict
