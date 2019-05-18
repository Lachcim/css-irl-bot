import json
import logging
import sys
import threading
import traceback
import praw
import requests

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

def validate_query(css):
    # send query to w3c for direct validation, return none on network error
    try:
        result = requests.post(
            "https://validator.w3.org/nu/",
            headers={"User-Agent": "cssirlbot"},
            files={
                "css": (None, "yes"),
                "out": (None, "json"),
                "content": (None, css),
                "useragent": (None, "cssirlbot"),
                "showsource": (None, "yes")
            }
        )
    except:
        return None
        
    # return true if there are no messages, return none on wrong status code, otherwise return false
    if result.status_code == 200:
        parsed_result = json.loads(result.text)
        
        return len(parsed_result["messages"]) == 0, parsed_result["messages"]
    else:
        return None
    
def validate_title(title):
    # check title as it is
    result, errors = validate_query(title)
    
    # finish validation on success or network error
    if result != False:
        return result, errors
    
    # finish validation if there was no parse error
    parse_error = False
    for error in errors:
        if error["message"] == "Parse Error.":
            parse_error = True
            break
            
    if not parse_error:
        return result, errors
        
    # if there was a parse error, retry validation with dummy selector wrapped around
    new_result, new_errors = validate_query(".dummySelector { " + title + " }")
    
    # return result verbatim
    return new_result, new_errors
    
def format_error_string(errors):
    # format the errors using reddit markdown syntax
    message = ""
    message += config["strings"]["INVALID_CSS_MESSAGE_HEAD"]
    
    for error in errors:
        # protection against markdown injection, no way to escape the grave accent
        error["message"] = error["message"].replace("`", "'")
        
        message += config["strings"]["INVALID_CSS_MESSAGE_ENTRY"].format(**error)
    
    message += config["strings"]["INVALID_CSS_MESSAGE_TAIL"]
    message += config["strings"]["FOOTNOTE"]
    
    return message

def process_submission(submission):
    # validate submission
    result, errors = validate_title(submission.title)
    
    if result == None:
        logging.error("Error while validating")
        return
    
    try:
        # reply to submission
        if result == True and config["behavior"]["comment_on_valid_css"]:
            comment = submission.reply(config["strings"]["VALID_CSS_MESSAGE"] + config["strings"]["FOOTNOTE"])
        elif result == False and config["behavior"]["comment_on_invalid_css"]:
            comment = submission.reply(format_error_string(errors))
        
        # distinguish comment
        if config["behavior"]["distinguish_comments"]:
            comment.mod.distinguish(how="yes", sticky=config["behavior"]["sticky_comments"])
        
        # mark submission as processed
        submission.save()
        
        logging.info("Processed!")
        return True
    except praw.exceptions.APIException as e:
        if e.error_type == "RATELIMIT":
            # rate limit reached, stop processing and wait for next batch
            
            logging.warning("Rate limit reached")
            return False
        elif e.error_type in ["TOO_OLD", "THREAD_LOCKED"]:
            # prevent bot from processing this submission again
            submission.save()
            
            logging.info("Post cannot be replied to")
            return True
        else:
            # other error
            
            logging.warning("Error processing submission")
            logging.info(traceback.format_exc())
            return True

def work():
    try:
        logging.info("Checking for new submissions")
        
        # get already processed submissions
        saved_submissions = list(reddit.user.me().saved())
        
        for submission in subreddit.new():
            if submission in saved_submissions:
                continue
            
            logging.info("New submission found: http://redd.it/" + submission.id)
            
            go_on = process_submission(submission)
            if not go_on:
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
