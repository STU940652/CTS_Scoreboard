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
        time = datetime.datetime.now().strftime("%M:%S.%f")[:-3]
        socketio.emit('update_scoreboard', {"lane_time3" : time}, namespace='/scoreboard')
        place += 1

@app.route('/')
def index():
    return render_template('scoreboard.html')

@socketio.on('start_scoreboard', namespace='/scoreboard')
def handle_my_custom_event(json):
    print('received scoreboard: ' + str(json))
    emit('update_scoreboard', {"lane_time3" : "2:34.567", "lane_time4" : "5:43.122", 'data': 'Connected'}, namespace='/scoreboard')
    print('sent message')

@socketio.on('connect', namespace='/scoreboard')
def test_connect():
    global main_thread
    print("Got one scoreboard")
    if(main_thread is None):
        main_thread = socketio.start_background_task(target=main_thread_worker)

if __name__ == '__main__':
    socketio.run(app)
