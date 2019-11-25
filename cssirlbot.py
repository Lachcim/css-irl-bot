import json
import logging
import sys
import threading
import traceback
import praw
import cssirlbot.processing
import cssirlbot.submissionhistory

# get config
with open("config.json") as file:
    config = json.loads(file.read())

# configure logging to file
logging.basicConfig(filename="cssirlbot.log",
    filemode="a",
    format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger().setLevel(config["internal"]["logging_level"])

# also log to stdout
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(config["internal"]["logging_level"])
stdout_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logging.getLogger().addHandler(stdout_handler)

def work():
    try:
        logging.info("Checking for new submissions")
        
        # check target subreddit for new submissions
        if config["behavior"]["process_submissions"]:
            for submission in subreddit.new():
                # ignore processed submissions
                if cssirlbot.submissionhistory.is_processed(submission):
                    continue
                
                logging.info("New submission found: http://redd.it/" + submission.id)
                
                # if error occurred during processing, abandon processing session
                if not cssirlbot.processing.process_submission(submission, config):
                    break
        
        # check username mentions
        if config["behavior"]["process_mentions"]:
            for mention in reddit.inbox.mentions():
                # ignore processed comments
                if cssirlbot.submissionhistory.is_processed(mention):
                    continue
                    
                logging.info("New mention found: https://reddit.com/r/all/comments/" + mention.submission.id + "/" + mention.id)
                
                # abandon session on error
                if not cssirlbot.processing.process_comment(mention, config, reddit.user.me().name):
                    break
    except:
        logging.error("Error in main loop: ")
        logging.info(traceback.format_exc())
        
    # restart this function after the configured interval
    threading.Timer(config["internal"]["feed_check_interval"], work).start()

logging.info("Bot starting")
    
reddit = praw.Reddit("cssirlbot", user_agent="linux:cssirlbot:1 (by /u/Lachcim)")
subreddit = reddit.subreddit(config["behavior"]["subreddit"])

logging.info("Bot online")

work()
