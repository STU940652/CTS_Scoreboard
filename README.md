# CTS_Scoreboard
HTML display of CTS scoreboard.

This is a command line utility to snoop the serial link between a Colorado Time Systems controller and scoreboard. It will then render the scoreboard to HTML using Javascript and a Websocket connection. Example use cases are creating an overlay for video streaming using OBS studio, secondary scoreboard, or scoreboard replacement. This project is in no way associated with CTS, etc. etc.

## Protocol
Interpretation of the protocol is based largely on the work of [hwbrill](https://github.com/hwbrill/vsCTS/blob/master/README.md) and [Marco](https://marcoscorner.walther-family.org/2015/07/colorado-timing-console-scoreboard-protocol/). 

## Hardware
To get the CTS serial stream, you need:
1) An RS-232 port, e.g. a USB to RS-232 cable.
2) A mono 1/4" male to two female Y cable, e.g.

   [Hosa YPP-111 1/4 inch TS to Dual 1/4 inch TSF Y Cable](https://www.amazon.com/dp/B000068O53?ref=yo_pop_ma_swf)
3) A male DB-9 connector, e.g.  

   [StarTech.com Assembled DB9 Female Solder D-SUB Connector with Plastic Backshell (C9PSF)]( https://www.amazon.com/dp/B00066HQ7S?ref=yo_pop_ma_swf)
   
Cut off one of the 1/4" female connectors. Solder the center conductor to pin 2 of the DB-9, and the shield to pin 5. Put it all together, connect it inline with the CTS cable, connect the DB-9 to the serial port, and you are done.

## Running the Program
usage: StreamServer.py [-h] [--port PORT] [--in IN_FILE] [--out OUT]
                       [--portlist]

Provide HTML rendering of Coloado Timing System data.

optional arguments:
  -h, --help            show this help message and exit
  --port PORT, -p PORT  Serial port input from CTS scoreboard
  --in IN_FILE, -i IN_FILE
                        Input file to use instead of serial port
  --out OUT, -o OUT     Output file to dump data
  --portlist, -l        List of available serial ports

## Page Templates
The HTML server is [Flask](http://flask.pocoo.org/), and the templates are based on [Jinja2](http://jinja.pocoo.org/docs/2.10/templates/). This makes it easy to make multiple displays based on need. At the moment there are two:

 /       Scoreboard display suitable for screen overlay
 /test   Scoreboard display overlayed on a static image for testing.
 
## Pips
pip install flask
pip install flask_login
pip install flask_socketio
pip install PySerial
(eventlet or gevent and gevent-websocket)
