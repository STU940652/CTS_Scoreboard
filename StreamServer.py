#!/usr/bin/env python
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, send, emit
import datetime
import curses

meet_title = "State College vs Lock Haven and Dubois"

app = Flask(__name__)
socketio = SocketIO(app)

main_thread = None
event_heat_info = [' ',' ',' ',' ',' ',' ',' ',' ']
lane_info = [[],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0],
            [0,0,0,0,0,0,0,0]]

stdscr = curses.initscr()

def hex_to_digit(c):
    c = c & 0x0F
    c ^= 0x0F # Invert lower nybble
    if (c > 9):
        return ' '
    return ("%i" % c)

def parse_line(l):
    global event_heat_info, lane_info
    update={}

    try:
        # Byte 0 - Channel
        c = l.pop(0)
        running_finish = True if (c & 0x40) else False
        format_display = True if (c & 0x01) else False
        channel = ((c & 0x3E) >> 1) ^ 0x1F
        
        if (1 <= channel <= 10) and not format_display:
            # This is a lane display of interest
            while len(l):
                c = l.pop(0)
                lane_info[channel][(c >> 4) & 0x0F] = c
            
            lane = hex_to_digit(lane_info[channel][0])
            place = hex_to_digit(lane_info[channel][1])
            
            time = hex_to_digit(lane_info[channel][2]) + hex_to_digit(lane_info[channel][3])
            time += ':' if time.strip() else ' '
            time += hex_to_digit(lane_info[channel][4]) + hex_to_digit(lane_info[channel][5])
            time += '.' if time.strip() else ' '
            time += hex_to_digit(lane_info[channel][6]) + hex_to_digit(lane_info[channel][7])

            update["lane_time%i"%channel] = time
            update["lane_place%i"%channel] = place
            
            #print("%2s:%s %s %s|" % (channel, lane, place, time), running_finish)
            stdscr.addstr(channel+1, 0, " " * 20)
            stdscr.addstr(channel+1, 0, "%4s: %s %s %s" % (channel, lane, place, time))
            stdscr.refresh()
        
        if (channel == 12) and not format_display:
            # Event / Heat
            while len(l):
                c = l.pop(0)
                event_heat_info[(c >> 4) & 0x0F] = hex_to_digit(c)
                
            update["current_event"] = ''.join(event_heat_info[:3])
            update["current_heat"] = ''.join(event_heat_info[-3:])

            stdscr.addstr(0, 0, " Event:" +  update["current_event"] + " Heat:" + update["current_heat"] + "    ")

            
    except IndexError:
        traceback.print_exc()
        
    finally:
        #Output anything we got
        if len(update):
            socketio.emit('update_scoreboard', update, namespace='/scoreboard')


def main_thread_worker():
    with open('minicom.system5.20150708', 'rb') as f:
        l = []
        while True:
            c = f.read(1)
            if not c:
                # End of file
                break
            c=c[0]

            if (c & 0x80) or (len(l) > 8):
                if len(l):
                    parse_line(l)
                    socketio.sleep(0.01)
                l=[]
                    
            l.append(c)      
            

@app.route('/')
def index():
    return render_template('scoreboard.html', meet_title=meet_title)

@app.route('/test')
def test():
    return render_template('scoreboard.html', meet_title=meet_title, test_background=True)    
    
@socketio.on('connect', namespace='/scoreboard')
def test_connect():
    global main_thread
    print("Scoreboard connected")
    if(main_thread is None):
        main_thread = socketio.start_background_task(target=main_thread_worker)

if __name__ == '__main__':
    socketio.run(app)
