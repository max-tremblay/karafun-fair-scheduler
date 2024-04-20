import argparse
import os
from scheduler import Scheduler
from flask import Flask, render_template
from waitress import serve

app = Flask(__name__)

parser = argparse.ArgumentParser(description='Karafun fair scheduler.')
parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='enable logging')
parser.add_argument('--hide-singers', action='store_true', help='hide who queued each song')
parser.add_argument('channel', help='karafun session id')
args = parser.parse_args()

print(__file__)
global s

@app.route("/")
def index():
    singers = [singer["singer"] for singer in s.get_current_queue()]
    return render_template("singers.html", singers=singers)

@app.route("/json")
def json_debug():
    return s.get_current_queue()

@app.route("/next/<id>")
def next(id):
    try:
        s.next(int(id))
        return "ok"
    except Exception as error:
        return f"Error {error=}"

if __name__ == '__main__':
    s = Scheduler(args)
    serve(app, host="127.0.0.1", port=8080)



