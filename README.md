# meww_bot_in_python

You need a bot token to start up the bot, below will be the steps for getting one.

1 - Go to https://discord.com/developers/applications and set up an application by clicking the "New Application" button at the top.


2 - Click "Bot" on the left side of the page.


3 - Create a new bot by clicking "Add Bot"


4 - Scroll down until you see "Privileged Gateway Intents"


5 - Enable "Server Members Intent" and "Message Content Intent"


6 - Scroll back up until you see "Token" if it is displaing a long list of characters copy that, that's your token.
if it isn't, then click "Reset Token" and follow the steps Discord gives you.


7 - Once you have the token copied, rename example_config.toml to config.toml and paste your token into the discord_token field under [tokens]



The genius token and spotify id/secret are optional, but if you want spotify support for the music module you need the spotify credentials

Steps for getting the spotify id/secret

1 - Go here https://developer.spotify.com/dashboard/applications and create a new application

2 - Once you're on the application page, click "edit settings" and add http://localhost:8888/callback under "Redirect URIs"

3 - Scroll down and click save

4 - On the left side of the screen there should be your Client Id, copy that and paste it into the config.toml

5 - When you're done with that go back to the spotify dashboard and click "Show Client Secret", copy that and paste it into the config.toml
and you should be done with the spotify credentials
