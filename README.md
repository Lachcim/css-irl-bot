# css-irl-bot
The CSS_IRL bot is a reddit bot that fetches new submissions from a subreddit and parses their titles to check if they are valid CSS. It can post a comment detailing the found errors and/or confirm the validity of the title. It can also parse comments when summoned.

<img src="https://1mi.pl/~lachcim/html/cssirlbot.png">

## Configuration
The bot can be configured through a file named **config.json** as well as **praw.ini**.

In config.json, you can configure the following settings:

* `subreddit`: The subreddit where the bot operates.
* `process_submissions`: Process posts.
* `comment_on_invalid_css`: Automatically comment on invalid titles.
* `comment_on_valid_css`: Automatically comment on valid titles.
* `distinguish_comments`: Mark comments as mod comments (requires the "posts" mod permission).
* `sticky_comments`: Sticky comments when processing posts.
* `process_mentions`: Process username mentions.
* `process_external_mentions`: Process mentions outside the home subreddit.
* `feed_check_interval`: How often the bot should check for new posts.
* `logging_level`: How detailed the logs should be.

You can also manage the strings used by the bot and create or remove aliases for its commands.

The praw.ini file describes the credentials used by the bot. It has the following format:
```ini
[cssirlbot]
client_id=XXX
client_secret=XXX
password=XXX
username=XXX
```
The client ID and secret can be obtained by [registering a reddit app](https://reddit.com/prefs/apps).

## Running the bot

Download the files and prepare your configuration. Before running the bot, you might want to run `pip install -r requirements.txt` to obtain the dependencies. To start the script, run:

```
python3 cssirlbot.py
```

The bot will try to fetch the newest 100 submissions, mentions and comment replies and parse all of them.
