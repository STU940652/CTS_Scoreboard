#!/usr/bin/env python
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, send, emit
import datetime

app = Flask(__name__)
socketio = SocketIO(app)

main_thread = None

def main_thread_worker():
    place = 1
    while True:
        socketio.sleep(0.1)
        time = datetime.datetime.now().strftime("%S.%f")[:-3]
        update={}
        update["current_event"] = int(datetime.datetime.now().second/10) + 1
        update["current_heat"] = datetime.datetime.now().second%10 + 1
        
        for i in range(1,9):
            update["lane_time%i"%i] = "%2i:%s" % (i, time)
            update["lane_place%i"%i] = (datetime.datetime.now().second + i) % 8
        socketio.emit('update_scoreboard', update, namespace='/scoreboard')
        place += 1

@app.route('/')
def index():
    return render_template('scoreboard.html')

@socketio.on('connect', namespace='/scoreboard')
def test_connect():
    global main_thread
    print("Scoreboard connected")
    if(main_thread is None):
        main_thread = socketio.start_background_task(target=main_thread_worker)

if __name__ == '__main__':
    socketio.run(app)
