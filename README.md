# Meww Bot

Pip dependencies before you start:
  - discord.py
  - lyricsgenius
  - numpy
  - pandas
  - reactionmenu
  - spotipy
  - toml
  - urlextract
  - yt_dlp

You need a bot token to start up the bot, below will be the steps for getting one.

1 - Go to https://discord.com/developers/applications and set up an application by clicking the "New Application" button at the top.


2 - Click "Bot" on the left side of the page.


3 - Create a new bot by clicking "Add Bot"


4 - Scroll down until you see "Privileged Gateway Intents"


5 - Enable "Server Members Intent" and "Message Content Intent"


6 - Scroll back up until you see "Token" if it is displaing a long list of characters copy that, that's your token.
if it isn't, then click "Reset Token" and follow the steps Discord gives you.


7 - Once you have the token copied, rename example_config.toml to config.toml and paste your token into the discord_token field under [tokens]

-----------------------------------------------------------------------------------------------------------------------------------------

The genius token and spotify id/secret are optional, but if you want spotify support for the music module you need the spotify credentials

Steps for getting the spotify id/secret

1 - Go here https://developer.spotify.com/dashboard/applications and create a new application

2 - Once you're on the application page, click "edit settings" and add http://localhost:8888/callback under "Redirect URIs"

3 - Scroll down and click save

4 - On the left side of the screen there should be your Client Id, copy that and paste it into the config.toml

5 - When you're done with that go back to the spotify dashboard and click "Show Client Secret", copy that and paste it into the config.toml
and you should be done with the spotify credentials

-----------------------------------------------------------------------------------------------------------------------------------------

Other Options in the Config

- prefix 
the prefix your bot uses, so if you have it as ~ the help command would be "~help" if you had it as ! it would be "!help"

- [spam_settings]
  - antispam
    - set this to true if you want to enable antispam bot-wide, you can still disable/enable it per server too.
  
  - spam_count
    - this is the amount of the same message a person can send in a row before they would be muted for spamming.
 
- [level_system]
  - levels_on
    - set this on to enable the level_system bot-wide, it can still be disabled/enabled per server.
  
  - xp_per_message
    - this is a range of two integers, a user can receive xp between the two, whenever they gain xp
  
  - cooldown_in_seconds
    - this is the amount of seconds that a user has to wait before they can gain xp from talking in the server.
