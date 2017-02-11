#!/usr/bin/env python
# coding: utf-8

"""
   LogBot

   A minimal IRC log bot

   Written by Chris Oliver

   Includes python-irclib from http://python-irclib.sourceforge.net/

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; either version 2
   of the License, or any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA   02111-1307, USA.
"""


__author__ = "Chris Oliver <excid3@gmail.com>"
__version__ = "0.5"
__date__ = "08/11/2009"
__copyright__ = "Copyright (c) Chris Oliver"
__license__ = "GPL2"


import cgi
import os
import ftplib
import sys
import itertools
import time
from time import strftime
try:
    from datetime import datetime
    from pytz import timezone
except: pass

try:
    from hashlib import md5
except:
    import md5

from ircbot import SingleServerIRCBot
from irclib import nm_to_n

import re

pat1 = re.compile(r"(^|[\n ])(([\w]+?://[\w\#$%&~.\-;:=,?@\[\]+]*)(/[\w\#$%&~/.\-;:=,?@\[\]+]*)?)", re.IGNORECASE | re.DOTALL)

#urlfinder = re.compile("(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))")

def urlify2(value):
    return pat1.sub(r'\1<a href="\2" target="_blank">\3</a>', value)
    #return urlfinder.sub(r'<a href="\1">\1</a>', value)

### Configuration options
DEBUG = False

# IRC Server Configuration
SERVER = "metis.ii.uam.es"
PORT = 6667
SERVER_PASS = None
CHANNELS=["#redes2"]
BCAST_CHANS=["#redes2"]
MAIN_CHANNEL = "#redes2"
NICK = "logbot"
NICKS = ["logbot", "logbot_", "logbot__", "logbot___"]
ADMIN_NICKs = ["aserver", "aserver_", "aserver__", "aserver___", ]
NICK_PASS = ""

# Folder to save logs
LOG_FOLDER = "/home/arave/webapps/redes2logs/logs"

# The message returned when someone messages the bot
HELP_MESSAGE = "Soy un bot. Visita redes2.initelia.com para ver los chat logs"

# FTP Configuration
FTP_SERVER = ""
FTP_USER = ""
FTP_PASS = ""
# This folder and sub folders for any channels MUST be created on the server
FTP_FOLDER = ""
# The amount of messages to wait before uploading to the FTP server
FTP_WAIT = 25

CHANNEL_LOCATIONS_FILE = os.path.expanduser("~/.logbot-channel_locations.conf")
DEFAULT_TIMEZONE = 'UTC'

default_format = {
    "help" : HELP_MESSAGE,
    "alt_help" : "Overheat!",
    "spam_count" : "Dejarme tranquilo un poco pls ;_;",
    "ad" : "[Recordatorio]: los chat logs a diario en redes2.initelia.com",
    "action" : '<span class="person" style="color:%color%">* %user% %message%</span>',
    "join" : '-!- <span class="join">%user%</span> [%host%] has joined %channel%',
    "kick" : '-!- <span class="kick">%user%</span> was kicked from %channel% by %kicker% [%reason%]',
    "mode" : '-!- mode/<span class="mode">%channel%</span> [%modes% %person%] by %giver%',
    "nick" : '<span class="nick">%old%</span> is now known as <span class="nick">%new%</span>',
    "part" : '-!- <span class="part">%user%</span> [%host%] has parted %channel%',
    "pubmsg" : '<span class="person" style="color:%color%">&lt;%user%&gt;</span> %message%',
    "pubnotice" : '<span class="notice">-%user%:%channel%-</span> %message%',
    "quit" : '-!- <span class="quit">%user%</span> has quit [%message%]',
    "topic" : '<span class="topic">%user%</span> changed topic of <span class="topic">%channel%</span> to: %message%',
}

html_header = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>%title%</title>
    <link href="horror.css" rel="stylesheet" type="text/css">
  </head>
  <body>
  <h1>%title%</h1>
  <a id="back" href="..">Back</a><br/>
      <footer>
            <h4 class="bottomMargin">
            alfonso.sebares@estudiante.uam.es | Codigo base: https://github.com/excid3/logbot 
            </h4>
      </footer>
  <div class="wrap">
  </div>
  </body>
</html>
"""
css_file = """
body {
    background-color: #F8F8FF;
    font-family: Fixed, monospace;
    font-size: 13px;
}
h1 {
    font-family: sans-serif;
    font-size: 28px;
    text-align: center;
}
a, .time {
    color: #525552;
    text-decoration: none;
}
a:hover, .time:hover { text-decoration: underline; }
.person { color: #DD1144; }
.join, .part, .quit, .kick, .mode, .topic, .nick { color: #42558C; }
.notice { color: #AE768C; }

.wrap {
    height: auto;
    margin: 0 auto -25px; /* footer height + space */
    min-height: 100%;
    padding: 0 0 25px; /* footer height + space */
    box-sizing: border-box;
    overflow: auto;
}

footer {
    background-color: #F8F8FF;
    font-family: Fixed, monospace;
    font-size: 13px;
    position:fixed;
    left:0px;
    bottom:0px;
    height:30px;
    width:100%;
    text-align:center;
}

.footer {
    height: 30px;  /* footer height */
    padding-top: 20px;
    display: block;
    margin-top: 5px; /* space between content and footer */
    box-sizing: border-box;
}

#back {
    font-weight: bold;
    color: #000000; /*Negro*/
}"""

### Helper functions

def append_line(filename, line):
    data = open(filename, "rb").readlines()[:-3]
    data += [line, "\n<br />", "\n</div>", "\n</body>", "\n</html>"]
    write_lines(filename, data)

def write_lines(filename, lines):
    f = open(filename, "wb")
    f.writelines(lines)
    f.close()

def write_string(filename, string):
    f = open(filename, "wb")
    f.write(string)
    f.close()

color_pattern = re.compile(r'(\[\d{1,2}m)')
"Pattern that matches ANSI color codes and the text that follows"

def pairs(items):
    """
    Return pairs from items

    >>> list(pairs([1,2,3,4]))
    [(1, 2), (3, 4)]
    """
    items = iter(items)
    while True:
        yield next(items), next(items)

def html_color(input):
    """
    >>> html_color("This is plain but [30m this is in color")
    'This is plain but <span style="color: #000316"> this is in color</span>'
    >>> html_color("[32mtwo[37mcolors")
    '<span style="color: #00aa00">two</span><span style="color: #F5F1DE">colors</span>'
    """
    first = []
    parts = color_pattern.split(input)
    if len(parts) % 2:
        # an odd number of parts occurred - first part is uncolored
        first = [parts.pop(0)]
    rest = itertools.starmap(replace_color, pairs(parts))
    return ''.join(itertools.chain(first, rest))

def replace_color(code, text):
    code = code.lstrip('[').rstrip('m')
    colors = {
        '30': '000316',
        '31': 'aa0000',
        '32': '00aa00',
        '33': 'aa5500',
        '34': '0000aa',
        '35': 'E850A8',
        '36': '00aaaa',
        '37': 'F5F1DE',
    }
    if code not in colors:
        return text
    return '<span style="color: #%(color)s">%(text)s</span>' % dict(
        color = colors[code],
        text = text,
    )


### Logbot class

class Logbot(SingleServerIRCBot):
    def __init__(self, server, port, server_pass=None, channels=[],
                 nick="timber", nick_pass=None, format=default_format):
        SingleServerIRCBot.__init__(self,
                                    [(server, port, server_pass)],
                                    nick,
                                    nick)

        self.chans = [x.lower() for x in channels]
        self.format = format
        self.set_ftp()
        self.count = 0
        self.nick_pass = nick_pass

        #Added
        self.LAST_MSG = None
        self.LAST_AD = None
        self.HOUR_INTERVAL = 2
        self.spam_count = 0

        self.dispatch = None

        self.load_channel_locations()
        print "Logbot %s" % __version__
        print "Connecting to %s:%i..." % (server, port)
        print "Press Ctrl-C to quit"

    def quit(self):
        self.connection.disconnect("Quitting...")

    def color(self, user):
        return "#%s" % md5(user).hexdigest()[:6]

    def set_ftp(self, ftp=None):
        self.ftp = ftp

    ## ADMIN COMMANDS SECTION
    def do_command_err(self, c, e):
        err_msg = "Comando no reconocido :thinking:"
        c.privmsg(e.target(), err_msg)
        self.force_pubmsg_log(BCAST_CHANS, NICK, err_msg)

    def do_robodance(self, c, e):
        dance_msg = "♬ ♩ └[∵┌]└[ ∵ ]┘[┐∵]┘ ♪ ♫"
        c.privmsg(e.target(), dance_msg)
        self.force_pubmsg_log(BCAST_CHANS, NICK, dance_msg)

    def do_logreminder(self, c, e):
        reminder_msg = "Echa un vistazo a los logs de hoy en http://redes2.initelia.com/%23redes2/"+time.strftime("%Y-%m-%d")+".html"
        c.privmsg(e.target(), reminder_msg)
        self.force_pubmsg_log(BCAST_CHANS, NICK, reminder_msg)

    ## DICT WITH ADMIN FUNCTIONS
    def init_admin(self):
        self.dispatch = {
            "!robodance": self.do_robodance,
            "!reminder": self.do_logreminder,
        }

    #Admin command parse and fire
    def admin_command(self, c, e):
        self.init_admin()
        words = e.arguments()[0].split()
        command = words[0]

        if command not in self.dispatch:
            self.do_command_err(c,e)
        else:
            self.dispatch[command](c,e)

    ##OTHER FUNCTIONS FOR BOT MANAGEMENT

    #Force to log a broadcast message ("pubmsg") with no direct
    #triggering event that were not being logged previously (pre 0.5)
    #(e.g. welcome msg after join, answering a tag, etc)
    #   chans - MUST be a list, channels to broadcast
    #   user  - usually 'NICK' of the bot
    def force_pubmsg_log(self, chans, user, msg_str):
        msg = self.format["pubmsg"]
        msg = msg.replace("%user%", NICK)
        msg = msg.replace("%color%", self.color(NICK))
        user_msg = cgi.escape(msg_str)
        msg = msg.replace("%message%", html_color(user_msg))
        
        msg = urlify2(msg)

        for chan in chans:
            self.append_log_msg(chan, msg)

    def format_event(self, name, event, params):
        msg = self.format[name]
        for key, val in params.iteritems():
            msg = msg.replace(key, val)

        # Always replace %user% with e.source()
        # and %channel% with e.target()
        msg = msg.replace("%user%", nm_to_n(event.source()))
        msg = msg.replace("%host%", event.source())
        try: msg = msg.replace("%channel%", event.target())
        except: pass
        msg = msg.replace("%color%", self.color(nm_to_n(event.source())))
        try:
            user_message = cgi.escape(event.arguments()[0])
            msg = msg.replace("%message%", html_color(user_message))
        except: pass

        return msg

    def write_event(self, name, event, params={}):
        # Format the event properly
        if name == 'nick' or name == 'quit':
          chans = params["%chan%"]
        else:
          chans = event.target()
        msg = self.format_event(name, event, params)
        msg = urlify2(msg)

        # In case there are still events that don't supply a channel name (like /quit and /nick did)
        if not chans or not chans.startswith("#"):
            chans = self.chans
        else:
            chans = [chans]

        for chan in chans:
            self.append_log_msg(chan, msg)

        self.count += 1

        if self.ftp and self.count > FTP_WAIT:
            self.count = 0
            print "Uploading to FTP..."
            for root, dirs, files in os.walk("logs"):
                #TODO: Create folders

                for fname in files:
                    full_fname = os.path.join(root, fname)

                    if sys.platform == 'win32':
                        remote_fname = "/".join(full_fname.split("\\")[1:])
                    else:
                        remote_fname = "/".join(full_fname.split("/")[1:])
                    if DEBUG: print repr(remote_fname)

                    # Upload!
                    try: self.ftp.storbinary("STOR %s" % remote_fname, open(full_fname, "rb"))
                    # Folder doesn't exist, try creating it and storing again
                    except ftplib.error_perm, e: #code, error = str(e).split(" ", 1)
                        if str(e).split(" ", 1)[0] == "553":
                            self.ftp.mkd(os.path.dirname(remote_fname))
                            self.ftp.storbinary("STOR %s" % remote_fname, open(full_fname, "rb"))
                        else: raise e
                    # Reconnect on timeout
                    except ftplib.error_temp, e: self.set_ftp(connect_ftp())
                    # Unsure of error, try reconnecting
                    except:                      self.set_ftp(connect_ftp())

            print "Finished uploading"

    def append_log_msg(self, channel, msg):
        if DEBUG: print "%s >>> %s" % (channel, msg)
        #Make sure the channel is always lowercase to prevent logs with other capitalisations to be created
        channel_title = channel
        channel = channel.lower()

        # Create the channel path if necessary
        chan_path = "%s/%s" % (LOG_FOLDER, channel)
        if not os.path.exists(chan_path):
            os.makedirs(chan_path)

            # Create channel index
            write_string("%s/index.html" % chan_path, html_header.replace("%title%", "%s | Logs" % channel_title))

            #Create css
            write_lines("%s/horror.css" % chan_path, css_file)

            # Append channel to log index
            append_line("%s/index.html" % LOG_FOLDER, '<a href="%s/index.html">%s</a>' % (channel.replace("#", "%23"), channel_title))

        # Current log
        try:
            localtime = datetime.now(timezone(self.channel_locations.get(channel,DEFAULT_TIMEZONE)))
            time = localtime.strftime("%H:%M:%S")
            date = localtime.strftime("%Y-%m-%d")
        except:
            time = strftime("%H:%M:%S")
            date = strftime("%Y-%m-%d")

        log_path = "%s/%s/%s.html" % (LOG_FOLDER, channel, date)

        # Create the log date index if it doesnt exist
        if not os.path.exists(log_path):
            write_string(log_path, html_header.replace("%title%", "%s | Logs for %s" % (channel_title, date)))

            #Create css
            write_lines("%s/horror.css" % chan_path, css_file)

            # Append date log
            append_line("%s/index.html" % chan_path, '<a href="%s.html">%s</a>' % (date, date))

        # Append current message
        message = "<a href=\"#%s\" name=\"%s\" class=\"time\">[%s]</a> %s" % \
                                          (time, time, time, msg)
        append_line(log_path, message)


    def welcome(self, c, e):
        welcome_msg = "Bienvenido %s :)" % nm_to_n(e.source())
        if self.LAST_AD is not None:
            timestamp2 = datetime.now().ctime()
            t1 = datetime.strptime(self.LAST_AD, "%a %b  %d %H:%M:%S %Y")
            t2 = datetime.strptime(timestamp2, "%a %b  %d %H:%M:%S %Y")
            diff = t2 - t1

            if diff.seconds/60/60 >= 2:
                c.privmsg(MAIN_CHANNEL, welcome_msg)
                self.force_pubmsg_log(BCAST_CHANS, NICK, welcome_msg)
                self.LAST_AD = datetime.now().ctime()
        else:
            #c.send_raw(self.format["ad"])
            c.privmsg(MAIN_CHANNEL, welcome_msg)
            self.force_pubmsg_log(BCAST_CHANS, NICK, welcome_msg)
            self.LAST_AD = datetime.now().ctime()
        return

    ### These are the IRC events

    def on_all_raw_messages(self, c, e):
        """Display all IRC connections in terminal"""
        if DEBUG: print e.arguments()[0]

    def on_welcome(self, c, e):
        """Join channels after successful connection"""
        if self.nick_pass:
          c.privmsg("nickserv", "identify %s" % self.nick_pass)

        for chan in self.chans:
            c.join(chan)

    def on_nicknameinuse(self, c, e):
        """Nickname in use"""
        c.nick(c.get_nickname() + "_")

    def on_invite(self, c, e):
        """Arbitrarily join any channel invited to"""
        c.join(e.arguments()[0])
        #TODO: Save? Rewrite config file?

    ### Loggable events

    def on_action(self, c, e):
        """Someone says /me"""
        self.write_event("action", e)

    def on_join(self, c, e):
        self.write_event("join", e)
        #Avoid welcoming itself
        if nm_to_n(e.source()) not in NICKS:
            self.welcome(c,e)
        #debug c.privmsg("#pruebas", "Alguien se ha conectado!")
        

    def on_kick(self, c, e):
        self.write_event("kick", e,
                         {"%kicker%" : e.source(),
                          "%channel%" : e.target(),
                          "%user%" : e.arguments()[0],
                          "%reason%" : e.arguments()[1],
                         })

    def on_mode(self, c, e):
        self.write_event("mode", e,
                         {"%modes%" : e.arguments()[0],
                          "%person%" : e.arguments()[1] if len(e.arguments()) > 1 else e.target(),
                          "%giver%" : nm_to_n(e.source()),
                         })

    def on_nick(self, c, e):
        old_nick = nm_to_n(e.source())
        # Only write the event on channels that actually had the user in the channel
        for chan in self.channels:
            if old_nick in [x.lstrip('~%&@+') for x in self.channels[chan].users()]:
                self.write_event("nick", e,
                             {"%old%" : old_nick,
                              "%new%" : e.target(),
                              "%chan%": chan,
                             })

    def on_part(self, c, e):
        self.write_event("part", e)

    #TO-DO: reshape, maybe
    def on_pubmsg(self, c, e):
        self.write_event("pubmsg", e)
        #process normal bot mention
        if e.arguments()[0].startswith(NICK):
            if self.LAST_MSG is not None:
                timestamp2 = datetime.now().ctime()
                t1 = datetime.strptime(self.LAST_MSG, "%a %b  %d %H:%M:%S %Y")
                t2 = datetime.strptime(timestamp2, "%a %b  %d %H:%M:%S %Y")
                diff = t2 - t1

                if diff.seconds > 30:
                    self.LAST_MSG = datetime.now().ctime()
                    self.spam_count = 0
                    c.privmsg(e.target(), self.format["help"])
                    self.force_pubmsg_log(BCAST_CHANS, NICK, self.format["help"])
                else:
                    self.spam_count += 1
                    if self.spam_count >= 3:
                        c.privmsg(e.target(), self.format["spam_count"])
                        self.force_pubmsg_log(BCAST_CHANS, NICK, self.format["spam_count"])
                        self.spam_count = 0
            else:
                self.LAST_MSG = datetime.now().ctime()
                c.privmsg(e.target(), self.format["help"])
                self.force_pubmsg_log(BCAST_CHANS, NICK, self.format["help"])
        else:
            #process bot command
            if e.arguments()[0][0] == '!':
                #process admin command
                if nm_to_n(e.source()) in ADMIN_NICKs:
                    self.admin_command(c,e)
                #process normal user command:
                else:
                    pass #self.normal_command(c,e)
        return

    def on_pubnotice(self, c, e):
        self.write_event("pubnotice", e)

    #Timeouts go here?
    def on_privmsg(self, c, e):
        print nm_to_n(e.source()), e.arguments()
        c.privmsg(nm_to_n(e.source()), self.format["help"])
        self.write_event("pubmsg", e)

    def on_quit(self, c, e):
        nick = nm_to_n(e.source())
        # Only write the event on channels that actually had the user in the channel
        for chan in self.channels:
            if nick in [x.lstrip('~%&@+') for x in self.channels[chan].users()]:
                self.write_event("quit", e, {"%chan%" : chan})

    def on_topic(self, c, e):
        self.write_event("topic", e)

    # Loads the channel - timezone-location pairs from the CHANNEL_LOCATIONS_FILE
    # See the README for details and example
    def load_channel_locations(self):
        self.channel_locations = {}
        if os.path.exists(CHANNEL_LOCATIONS_FILE):
            f = open(CHANNEL_LOCATIONS_FILE, 'r')
            self.channel_locations = dict((k.lower(), v) for k, v in dict([line.strip().split(None,1) for line in f.readlines()]).iteritems())

def connect_ftp():
    print "Using FTP %s..." % (FTP_SERVER)
    f = ftplib.FTP(FTP_SERVER, FTP_USER, FTP_PASS)
    f.cwd(FTP_FOLDER)
    return f

def main():
    # Create the logs directory
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
        write_string("%s/index.html" % LOG_FOLDER, html_header.replace("%title%", "IRC Chat Logs"))

        #Create css
        write_lines("%s/horror.css" % LOG_FOLDER, css_file)


    # Start the bot
    bot = Logbot(SERVER, PORT, SERVER_PASS, CHANNELS, NICK, NICK_PASS)
    try:
        # Connect to FTP
        if FTP_SERVER:
            bot.set_ftp(connect_ftp())

        bot.start()
    except KeyboardInterrupt:
        if FTP_SERVER: bot.ftp.quit()
        print "\nClosing..."
        bot.quit()


if __name__ == "__main__":
    main()
