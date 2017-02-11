easyBot 0.5
============

Sections of this README are relayed from the original code repository which served as starting point for this implementation.
Original code written by Chris Oliver with Filip Slagter contributions:
https://github.com/excid3/logbot

Usage
-----
easyBot requires Python 2. It is NOT compatible with Python 3.
Configuration is done inside logbot.py.

    python logbot.py


Channels with localised time
-----
LogBot now also supports having localised time on a per channel basis using the pytz library, allowing you to have the logs of specific channels use different timezones.
Installing pytz should be as simple as running `easy_install --upgrade pytz`, see http://pytz.sourceforge.net/#installation for details.
Don't worry, if you don't have pytz installed, LogBot will continue to show the logs timestamped with your system's localtime as it used to.

Next you can create a simple text file at `~/.logbot-channel_locations.conf` (or wherever `CHANNEL_LOCATIONS_FILE` in logbot.py points to).
On each line you can now specify a channel name, and the timezone location of which it should use the timezone offset, separated by a space. Example:

	#excid3 America/Chicago
	#netherlands Europe/Amsterdam
	#aloha US/Hawaii
	#space UTC

Any channel not specified in this file will use the default timezone as specified in DEFAULT_TIMEZONE, which defaults to 'UTC'.

If you want to see a list of all possible timezone location names you can use, run:

    python -c 'import pytz;print pytz.all_timezones'
