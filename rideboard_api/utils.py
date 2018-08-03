from functools import wraps

from flask import session

def user_auth(func):
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        last = session["userinfo"].get("family_name", "")
        first = session["userinfo"].get("given_name", "")
        uid = session["userinfo"].get("preferred_username", "")
        is_rtp = 'rtp' in session["userinfo"].get("groups", "")

        metadata = {
            "first": first,
            "last": last,
            "uid": uid,
            "is_rtp": is_rtp
        }
        kwargs["metadata"] = metadata

        return func(*args, **kwargs)

    return wrapped_function
