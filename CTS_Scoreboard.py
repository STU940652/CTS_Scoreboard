#! /usr/bin/python3
import flask
import flask_login
import flask_socketio
import datetime
import traceback
import ctypes
import serial
import serial.tools.list_ports
import re
import time
import json
import os.path
import glob
from hytek_event_loader import HytekEventLoader
import ap

DEBUG = False
#DEBUG = True
settings_file = './settings.json'

settings = {
    'meet_title': '',
    'serial_port': 'COM1',
    'username': 'admin',
    'password': 'password'
    }
in_file = None
out_file = None
in_speed = 1.0
debug_console = False

# Event Settings
event_info = HytekEventLoader()

app = flask.Flask(__name__)
# config
app.config.update(
    DEBUG = False,
    SECRET_KEY = 'rimnqiuqnewiornhf7nfwenjmqvliwynhtmlfnlsklrmqwe'
)
socketio = flask_socketio.SocketIO(app)

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

def load_settings():
    global settings
    try:
        with open(settings_file, "rt") as f:
            settings.update(json.load(f))
        if 'event_info' in settings:
            event_info.from_object(settings['event_info'])
    except: pass

## Stuff to move the cursor
def print_at(r, c, s):
    if debug_console:
        ap.output(c, r, s)   
            
def hex_to_digit(c):
    c = c & 0x0F
    c ^= 0x0F # Invert lower nybble
    if (c > 9):
        return ' '
    return ("%i" % c)

update={}
next_update = datetime.datetime.now()
last_event_sent = (0,0)

def parse_line(l, out = None):
    global event_heat_info, lane_info, time_info, running_time, update, next_update, last_event_sent
    
    s = ""
    if out:
        k = "[%f] "% time.time() + " ".join(["%02X" % int(c) for c in l])
        out.write(k)
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
            
            update["lane_place%i"%channel] = place
            update["lane_running%i"%channel] = running_finish
            
            if running_finish:
                lane_time = running_time # '        '
                s = "%4s: running" % (channel)
            else:
                lane_time = hex_to_digit(lane_info[channel][2]) + hex_to_digit(lane_info[channel][3])
                lane_time += ':' if lane_time.strip() else ' '
                lane_time += hex_to_digit(lane_info[channel][4]) + hex_to_digit(lane_info[channel][5])
                lane_time += '.' if lane_time.strip() else ' '
                lane_time += hex_to_digit(lane_info[channel][6]) + hex_to_digit(lane_info[channel][7])
                s = "%4s: %s %s %s" % (channel, lane, place, lane_time)
                update["lane_time%i"%channel] = lane_time
                
            print_at(channel+1, 0, " " * 20)
            print_at(channel+1, 0, "%4s: %s %s %s" % (channel, lane, place, lane_time))
            
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
            
            s = "Running Time: " + running_time

        if (channel == 12) and not format_display:
            # Event / Heat
            while len(l):
                c = l.pop(0)
                event_heat_info[(c >> 4) & 0x0F] = hex_to_digit(c)
                
            update["current_event"] = ''.join(event_heat_info[:3])
            update["current_heat"] = ''.join(event_heat_info[-3:])
            try:
                event_tuple = (int(update["current_event"]), int(update["current_heat"]))
            except: return

            print_at(0, 0, " Event:" +  update["current_event"] + " Heat:" + update["current_heat"] + "    ")
            
            s = " Event:" +  update["current_event"] + " Heat:" + update["current_heat"] + "    "
            
            if last_event_sent != event_tuple:
                last_event_sent = event_tuple
                update["event_name"] = event_info.get_event_name(event_tuple[0])
                
                for i in range(1,11):
                    update["lane_name%i" % i] = event_info.get_display_string(event_tuple[0], event_tuple[1], i)

        if out:
            if s:
                out.write(' '*max(0, 50-len(k)) + " # " + s)
            out.write("\n")
    except IndexError:
        traceback.print_exc()
        
    finally:
        #Output anything we got
        if "current_event" in update or "running_time" in update:
            socketio.emit('update_scoreboard', update, namespace='/scoreboard')
            update.clear()
            
        if (datetime.datetime.now() > next_update) and debug_console:
            next_update = datetime.datetime.now() + datetime.timedelta(seconds=0.2)
            ap.render()


def main_thread_worker():
    j = None
    if in_file:
        delay = 0.0
        start_time = None
        with open(in_file, 'rt') as f:
            if out_file:
                j = open(out_file, "at")
            l = []
            for d in re.finditer(r"\[([0-9.]+)\]\s*|([0-9a-fA-F]{2})\s+", f.read()):
                if d.group(1):
                    if start_time:
                        delay = float(d.group(1)) - in_speed*time.time() - start_time
                        if delay > 0:
                            socketio.sleep(delay)
                        print_at(13, 0, " " + d.group(1) + "   ")
                    else:
                        start_time = float(d.group(1)) - in_speed*time.time()
                    continue
                c = int(d.group(2), 16)
                if c:
                    if (c & 0x80) or (len(l) > 8):
                        if len(l):
                            parse_line(l, j)
                        l=[]
                    l.append(c)
                if delay > (0.1):
                    delay = 0
                    socketio.sleep(0.1) # 9600 = about 1ms per character
                else:
                    delay += 1/9600.0
    else:
        with serial.Serial(settings['serial_port'], 9600, timeout=0) as f:
            if out_file:
                j = open(out_file, "at")
            l = []
            while True:
                c = f.read(1)
                if c:
                    c=c[0]
                    if (c & 0x80) or (len(l) > 8):
                        if len(l):
                            parse_line(l, j)
                        l=[]
                    l.append(c)
                else:
                    socketio.sleep(0.01)
            
# flask-login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "route_login"


# simple user model
class User(flask_login.UserMixin):

    def __init__(self, id):
        self.id = id
        self.name = settings['username']
        self.password = settings['password']
        
    def __repr__(self):
        return "%d/%s" % (self.id, self.name)


# create the user       
user = User(0)
            
            
@socketio.on('connect', namespace='/scoreboard')
def ws_scoreboard():
    global main_thread
    if(main_thread is None):
        main_thread = socketio.start_background_task(target=main_thread_worker)

@socketio.on('next_heat', namespace='/scoreboard')
def ws_next_heat(d):
    global last_event_sent
    
    update={}
    
    event_list = list(event_info.events.keys())
    event_list.sort()

    try:
        event_tuple = event_list[event_list.index(last_event_sent)+1]
    except:
        event_tuple = event_list[0]
    
    last_event_sent = event_tuple
    update["current_event"] = str(event_tuple[0])
    update["current_heat"] = str(event_tuple[1])
    update["event_name"] = event_info.get_event_name(event_tuple[0])
    
    for i in range(1,11):
        update["lane_name%i" % i] = event_info.get_display_string(event_tuple[0], event_tuple[1], i)

    socketio.emit('update_scoreboard', update, namespace='/scoreboard')


        
# Scoreboard Templates
@app.route('/overlay/<name>')
def route_overlay(name):
    overlay_name = "overlay/" + name + '.html'
    return flask.render_template(overlay_name, meet_title=settings['meet_title'], test_background='test' in flask.request.args.keys())
    
@app.route('/settings', methods=['POST', 'GET'])
@flask_login.login_required
def route_settings():
    global settings
    if flask.request.method == 'POST':
        modified = False
        
        # check if the post request has the file part
        if 'meet_schedule' in flask.request.files:
            file = flask.request.files['meet_schedule']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file and file.filename and file.filename.endswith('.csv'):
                event_info.load_from_bytestream(file.stream)
                settings['event_info'] = event_info.to_object()
                modified = True
        
        for k in settings.keys(): 
            if k in flask.request.form and settings[k]!=flask.request.form.get(k):
                settings[k]=flask.request.form.get(k)
                modified = True
        
        if modified:
            with open(settings_file, "wt") as f:
                json.dump(settings, f, sort_keys=True, indent=4)
                
    comm_port_list = [(port, "%s: %s" % (port,desc)) for port, desc, id in serial.tools.list_ports.comports()]
    if settings['serial_port'] not in [port for port,desc in comm_port_list]:
        comm_port_list.insert(0, (settings['serial_port'], settings['serial_port']))
 
    return flask.render_template('settings.html', 
                meet_title=settings['meet_title'], 
                serial_port=settings['serial_port'],
                serial_port_list=comm_port_list,
                user_name=settings['username'])
                
@app.route('/schedule_clear')
@flask_login.login_required
def route_schedule_clear():
    event_info.clear()
    settings['event_info'] = event_info.to_object()
    with open(settings_file, "wt") as f:
        json.dump(settings, f, sort_keys=True, indent=4)
    return flask.redirect('/settings')
                
@app.route('/schedule_preview')
@flask_login.login_required
def route_schedule_preview():
    event_heat = list(event_info.events.keys())
    event_heat.sort()
    return flask.render_template('schedule_preview.html', 
                event_heat = event_heat, 
                event_names = event_info.event_names, 
                events = event_info.events)
    
# somewhere to login
@app.route("/login", methods=["GET", "POST"])
def route_login():
    if flask.request.method == 'POST':
        if ((flask.request.form['username']==settings['username']) and
            (flask.request.form['password']==settings['password'])):        
            user = User(0)
            flask_login.login_user(user)
            return flask.redirect(flask.request.args.get("next"))
        else:
            return flask.abort(401)
    else:
        return flask.render_template('login.html')


# somewhere to logout
@app.route("/logout")
@flask_login.login_required
def route_logout():
    flask_login.logout_user()
    return flask.redirect('/')


# handle login failed
@app.errorhandler(401)
def page_not_found(e):
    return flask.render_template('login.html', login_failed=True)
    

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

@app.route("/")
def route_site_map():
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = flask.url_for(rule.endpoint, **(rule.defaults or {}))
            title = rule.endpoint.replace("_"," ")
            if title.startswith('route '):
                title = title[6:]
            if title not in ['login','logout','site map']:
                links.append((url, title.title()))
                
    for file in glob.glob(os.path.join("templates", "overlay", "*.html")):
        links.append( (file[file.startswith("templates") and len("templates"):].rsplit('.',1)[0], "Overlay " + os.path.basename(file).rsplit('.',1)[0]) )
    # links is now a list of url, endpoint tuple
    links.sort(key=lambda a: '_' if (a[1] == 'Site List') else a[1])
    return flask.render_template('site_map.html', links=links)
    
# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return User(userid)
    
    
if __name__ == '__main__':
    import argparse
    
    load_settings()

    parser = argparse.ArgumentParser(description='Provide HTML rendering of Coloado Timing System data.')
    parser.add_argument('--port', '-p', action = 'store', default = '', 
        help='Serial port input from CTS scoreboard')
    parser.add_argument('--in', '-i', action = 'store', default = '', dest='in_file',
        help='Input file to use instead of serial port')
    parser.add_argument('--out', '-o', action = 'store', default = '', 
        help='Output file to dump data')
    parser.add_argument('--portlist', '-l', action = 'store_const', const=True, default = False,
        help='List of available serial ports')        
    parser.add_argument('--speed', '-s', action = 'store', default = 1.0, dest='in_speed',
        help='Speed to play input file at')
    parser.add_argument('--debug', '-d', action = 'store_const', const=True, default = False,
        help='Display debug info at console')
    args = parser.parse_args()

    try:
        if (args.portlist):
            print ("Available COM ports:")
            for port, desc, id in serial.tools.list_ports.comports():
                print (port, desc, id)
        if (args.port):
            settings['serial_port'] = args.port
        in_file = args.in_file
        out_file = args.out
        in_speed = float(args.in_speed)
        debug_console = args.debug
        ap.c()
        socketio.run(app, host="0.0.0.0")
    except:
        traceback.print_exc()
    finally:
        input('Press enter to continue...')
        
