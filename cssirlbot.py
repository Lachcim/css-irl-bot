import requests
import json
import praw
import threading

with open("config.json") as file:
    config = json.loads(file.read())

def validateQuery(css):
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
    
def validateTitle(title):
    # check title as it is
    result, errors = validateQuery(title)
    
    # finish validation on success or network error
    if result != False:
        return result, errors
    
    # finish validation if there was no parse error
    if errors[0]["message"] != "Parse Error.":
        return result, errors
        
    # if there was a parse error, retry validation with dummy selector wrapped around
    new_result, new_errors = validateQuery(".dummySelector { " + title + " }")
    
    # return result verbatim
    return new_result, new_errors
    
def formatErrorString(errors):
    # format the errors using reddit markdown syntax
    message = ""
    message += config["strings"]["INVALID_CSS_MESSAGE_HEAD"]
    
    for error in errors:
        # protection against markdown injection, no way to escape the grave accent
        error["message"] = error["message"].replace("`", "'")
        
        message += config["strings"]["INVALID_CSS_MESSAGE_ENTRY"].format(**error);
    
    message += config["strings"]["INVALID_CSS_MESSAGE_TAIL"]
    
    return message

def process_submission(submission):
    # validate submission
    result, errors = validateTitle(submission.title)
    
    if result == None:
        print("Error while validating")
        return
    
    # reply to submission
    if result == True and config["behavior"]["comment_on_valid_css"]:
        comment = submission.reply(config["strings"]["VALID_CSS_MESSAGE"])
    elif result == False and config["behavior"]["comment_on_invalid_css"]:
        comment = submission.reply(formatErrorString(errors))
    
    # distinguish comment
    if config["behavior"]["distinguish_comments"]:
        comment.mod.distinguish(how="yes", sticky=config["behavior"]["sticky_comments"])
    
    # mark submission as processed
    submission.save()
    
    print("Parsed!")

def work():
    print("Checking for new submissions")
    
    # get already processed submissions
    saved_submissions = list(reddit.user.me().saved())
    
    for submission in subreddit.stream.submissions():
        if submission in saved_submissions:
            continue
        
        print("New submission found: http://redd.it/" + submission.id)
        process_submission(submission)
        
    # restart this function after the configured interval
    threading.Timer(config["behavior"]["feed_check_interval"], work).start()
    
reddit = praw.Reddit("cssirlbot", user_agent="linux:cssirlbot:1 (by /u/Lachcim)")
subreddit = reddit.subreddit(config["behavior"]["subreddit"])

work()