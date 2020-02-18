import argparse
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

# parse arguments
argParser = argparse.ArgumentParser()
argParser.add_argument("--dry-run",
    dest="dry_run",
    action="store_true",
    help="collect available posts but don't process them")
args = argParser.parse_args()

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
                
                if args.dry_run:
                    cssirlbot.submissionhistory.mark_as_processed(submission)
                    logging.info("Collected.")
                    continue
                
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
                
                if args.dry_run:
                    cssirlbot.submissionhistory.mark_as_processed(mention)
                    logging.info("Collected.")
                    continue
                
                # abandon session on error
                if not cssirlbot.processing.process_comment(mention, config, reddit):
                    break
            
            # comment replies have to be handled separately
            for mention in reddit.inbox.comment_replies():
                # ignore processed comments
                if cssirlbot.submissionhistory.is_processed(mention):
                    continue
                    
                logging.info("New comment reply found: https://reddit.com/r/all/comments/" + mention.submission.id + "/" + mention.id)
                
                if args.dry_run:
                    cssirlbot.submissionhistory.mark_as_processed(mention)
                    logging.info("Collected.")
                    continue
                
                # abandon session on error
                if not cssirlbot.processing.process_comment(mention, config, reddit):
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
