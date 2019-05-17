# css-irl-bot
The CSS_IRL bot is a reddit bot that fetches new submissions from a subreddit and parses their titles to check if they are valid CSS. It can post a comment detailing the found errors and do whatever else you'd like to do.

<img src="https://1mi.pl/~lachcim/html/cssirlbot.png">

## Configuration
The bot can be confugured through a file named **config.json** as well as **praw.ini**.

In config.json, you can configure the following settings:

* `subreddit`: The subreddit where the bot operates.
* `comment_on_invalid_css`: Whether the bot should comment on invalid CSS submissions.
* `comment_on_valid_css`: Whether the bot should comment on valid CSS submissions.
* `distinguish_comments`: Mark comments left by the bot as moderator comments (requires the "posts" moderator permission).
* `sticky_comments`: Whether distinguished comments should be stickied as well.
* `feed_check_interval`: How often the bot should check for new posts.
* `logging_level`: How detailed the logs should be.

You can also manage the following strings:

* `INVALID_CSS_MESSAGE_HEAD`: Text at the start of an invalid CSS message.
* `INVALID_CSS_MESSAGE_ENTRY`: Text describing an individual error.
* `INVALID_CSS_MESSAGE_TAIL`: Text at the end of an invalid CSS message.
* `VALID_CSS_MESSAGE`: Text informing that the parsed title is valid CSS.

The praw.ini file describes the credentials used by the bot. It has the following format:
```
[cssirlbot]
client_id=XXX
client_secret=XXX
password=XXX
username=XXX
```
The client ID and secret can be obtained when registering a reddit app: https://reddit.com/prefs/apps/.

## Running the bot

Download the files and prepare your configuration. Before running the bot, you might want to run `pip install -r requirements.txt` to obtain the dependencies. To start the script, run:

```
python3 cssirlbot.py
```

The bot will try to fetch the newest 100 submissions and parse all of them.