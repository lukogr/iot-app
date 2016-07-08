#!/usr/bin/python
# Copyright (C) 2016 PSNC
# Krzysztof Dombek (PSNC) <kdombek_at_man.poznan.pl>
#
# IoT cloud monitoring tools

from datetime import timedelta
from flask import make_response, request, current_app
from flask import jsonify
from functools import update_wrapper

from flask import Flask
app = Flask(__name__)
app.debug = True

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

data = {
  "status": {
    "generator-user": {
      "account_created": False, # lxd container + TeamSpeak
      "iot": {
        "111222333": {
          "channel_created": False,  # channel on TeamSpeak
          "path_established": False   # network
        }
      }
    }, 
    "libelium-user": {
      "account_created": False, 
      "iot": {
        "403458164": {
          "channel_created": False, 
          "path_established": False
        }, 
        "403472527": {
          "channel_created": False, 
          "path_established": False
        }
      }
    }, 
    "spirent-user": {
      "account_created": False, 
      "iot": {
        "123456789": {
          "channel_created": False, 
          "path_established": False
        }
      }
    }
  }
}

@app.route("/data/json")
@crossdomain(origin='*')
def getJsonData():
    return jsonify(data)

if __name__ == "__main__":
    app.run()