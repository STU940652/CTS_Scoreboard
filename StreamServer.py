#!/usr/bin/env python
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, send, emit
import datetime
import traceback
from ctypes import *
import serial
import serial.tools.list_ports
import re
import time

DEBUG = False
#DEBUG = True

meet_title = "State College vs Bellefonte vs Juniata Valley"
serial_port = 'COM3'
in_file = None
out_file = None

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
time_info = [0,0,0,0,0,0,0,0]
running_time = '        '
channel_running = [False for i in range(10)]

## Windows stuff to move the cursor
STD_OUTPUT_HANDLE = -11
 
class COORD(Structure):
    pass
 
COORD._fields_ = [("X", c_short), ("Y", c_short)]
 
def print_at(r, c, s):
    h = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    windll.kernel32.SetConsoleCursorPosition(h, COORD(c, r))
 
    c = s.encode("windows-1252")
    windll.kernel32.WriteConsoleA(h, c_char_p(c), len(c), None, None)        
            
def hex_to_digit(c):
    c = c & 0x0F
    c ^= 0x0F # Invert lower nybble
    if (c > 9):
        return ' '
    return ("%i" % c)

update={}
next_update = datetime.datetime.now()

def parse_line(l):
    global event_heat_info, lane_info, time_info, running_time, update, next_update

    try:
        # Byte 0 - Channel
        c = l.pop(0)
        running_finish = True if (c & 0x40) else False
        format_display = True if (c & 0x01) else False
        channel = ((c & 0x3E) >> 1) ^ 0x1F
        
        if (1 <= channel <= 10) and not format_display:
            channel_running[channel-1] = running_finish
            # This is a lane display of interest
            while len(l):
                c = l.pop(0)
                lane_info[channel][(c >> 4) & 0x0F] = c
            
            lane = hex_to_digit(lane_info[channel][0])
            place = hex_to_digit(lane_info[channel][1])
            
            if running_finish:
                time = running_time # '        '
            else:
                time = hex_to_digit(lane_info[channel][2]) + hex_to_digit(lane_info[channel][3])
                time += ':' if time.strip() else ' '
                time += hex_to_digit(lane_info[channel][4]) + hex_to_digit(lane_info[channel][5])
                time += '.' if time.strip() else ' '
                time += hex_to_digit(lane_info[channel][6]) + hex_to_digit(lane_info[channel][7])

            update["lane_time%i"%channel] = time
            update["lane_place%i"%channel] = place
            
            print_at(channel+1, 0, " " * 20)
            print_at(channel+1, 0, "%4s: %s %s %s" % (channel, lane, place, time))

        if (channel == 0) and not format_display:
            # Running time
            while len(l):
                c = l.pop(0)
                time_info[(c >> 4) & 0x0F] = c
            running_time = hex_to_digit(time_info[2]) + hex_to_digit(time_info[3])
            running_time += ':' if running_time.strip() else ' '
            running_time += hex_to_digit(time_info[4]) + hex_to_digit(time_info[5])
            running_time += '.' if running_time.strip() else ' '
            running_time += hex_to_digit(time_info[6]) + hex_to_digit(time_info[7])
            update["running_time"] = running_time

        if (channel == 12) and not format_display:
            # Event / Heat
            while len(l):
                c = l.pop(0)
                event_heat_info[(c >> 4) & 0x0F] = hex_to_digit(c)
                
            update["current_event"] = ''.join(event_heat_info[:3])
            update["current_heat"] = ''.join(event_heat_info[-3:])

            print_at(0, 0, " Event:" +  update["current_event"] + " Heat:" + update["current_heat"] + "    ")

    except IndexError:
        traceback.print_exc()
        
    finally:
        #Output anything we got
        if len(update) and (datetime.datetime.now() > next_update):
            socketio.emit('update_scoreboard', update, namespace='/scoreboard')
            next_update = datetime.datetime.now() + datetime.timedelta(seconds=0.2)
            update.clear()


def main_thread_worker():
    if in_file:
        delay = 0.0
        with open(in_file, 'rt') as f:
            if out_file:
                j = open(out_file, "at")
            l = []
            for d in re.finditer("([0-9a-fA-F]{2}) *", f.read()):
                c = int(d.group(1), 16)
                if c:
                    if out_file:
                        j.write ("%02X " % int(c))

                    if (c & 0x80) or (len(l) > 8):
                        if len(l):
                            parse_line(l)
                        l=[]
                    l.append(c)
                if delay > (0.1):
                    delay = 0
                    socketio.sleep(0.1) # 9600 = about 1ms per character
                else:
                    delay += 1/9600.0
    else:
        with serial.Serial(serial_port, 9600, timeout=0) as f:
            if out_file:
                j = open(out_file, "at")
            l = []
            while True:
                c = f.read(1)
                if c:
                    c=c[0]
                    if out_file:
                        j.write ("%02X " % int(c))

                    if (c & 0x80) or (len(l) > 8):
                        if len(l):
                            parse_line(l)
                        l=[]
                    l.append(c)
                else:
                    socketio.sleep(0.01)
            

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
    import argparse

    parser = argparse.ArgumentParser(description='Provide HTML rendering of Coloado Timing System data.')
    parser.add_argument('--port', '-p', action = 'store', default = 'COM3', 
        help='Serial port input from CTS scoreboard')
    parser.add_argument('--in', '-i', action = 'store', default = '', dest='in_file',
        help='Input file to use instead of serial port')
    parser.add_argument('--out', '-o', action = 'store', default = '', 
        help='Output file to dump data')
    parser.add_argument('--portlist', '-l', action = 'store_const', const=True, default = False,
        help='List of available serial ports')        
    args = parser.parse_args()

    try:
        if (args.portlist):
            print ("Available COM ports:")
            for port, desc, id in serial.tools.list_ports.comports():
                print (port, desc, id)
        
        serial_port = args.port
        in_file = args.in_file
        out_file = args.out
        socketio.run(app, host="0.0.0.0")
    except:
        traceback.print_exc()
    finally:
        input()
        