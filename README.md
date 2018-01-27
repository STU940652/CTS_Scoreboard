# CTS_Scoreboard
HTML display of CTS scoreboard.

This is a command line utility to snoop the serial link between a Colorado Timing Systems controller and scoreboard. It will then render the scoreboard to HTML using Javascript and a Websocket connection. Example use cases are creating an overlay for video streaming using OBS studio, secondary scoreboard, or scoreboard replacement.

# Hardware
To get the CTS serial stream, you need:
1) An RS-232 port, e.g. a USB to RS-232 cable.
2) A mono 1/4" male to two female Y cable, e.g.

   [Hosa YPP-111 1/4 inch TS to Dual 1/4 inch TSF Y Cable](https://www.amazon.com/dp/B000068O53?ref=yo_pop_ma_swf)
3) A male DB-9 connector, e.g.  

   [StarTech.com Assembled DB9 Female Solder D-SUB Connector with Plastic Backshell (C9PSF)]( https://www.amazon.com/dp/B00066HQ7S?ref=yo_pop_ma_swf)
   
Cut off one of the 1/4" female connectors. Solder the center conductor to pin 2 of the DB-9, and the shield to pin 5. Put it all together, connect it inline with the CTS cable, connect the DB-9 to the serial port, and you are done.
