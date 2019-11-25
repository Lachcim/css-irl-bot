﻿import logging
import praw
import cssirlbot.submissionhistory
import cssirlbot.validation

def process_submission(submission, config):
    # get config
    comment_on_valid = config["behavior"]["comment_on_valid_css"]
    comment_on_invalid = config["behavior"]["comment_on_invalid_css"]
    distinguish_comments = config["behavior"]["distinguish_comments"]
    sticky_comments = config["behavior"]["sticky_comments"]
    
    # validate submission
    result, errors = cssirlbot.validation.validate_title(submission.title)
    
    # signal failure if needed
    if result == None:
        logging.error("Error while validating")
        return False
    
    try:
        # reply to submission
        if result == True and comment_on_valid:
            comment = submission.reply(format_success_string(errors, config))
        elif result == False and comment_on_invalid:
            comment = submission.reply(format_error_string(errors, config))
        
        # distinguish comment
        if distinguish_comments:
            comment.mod.distinguish(how="yes", sticky=sticky_comments)
        
        # mark submission as processed
        cssirlbot.submissionhistory.mark_as_processed(submission)
        
        logging.info("Processed!")
        return True
    except praw.exceptions.APIException as e:
        if e.error_type == "RATELIMIT":
            # rate limit reached, stop processing and wait for next batch
            logging.warning("Rate limit reached")
            return False
        elif e.error_type in ["TOO_OLD", "THREAD_LOCKED"]:
            # prevent bot from processing this submission again
            cssirlbot.submissionhistory.mark_as_processed(submission)
            
            logging.info("Post cannot be replied to")
            return True
        else:
            # other error
            logging.warning("Error processing submission")
            logging.info(traceback.format_exc())
            return True
            
def format_success_string(errors, config):
    return config["strings"]["VALID_CSS_MESSAGE"] + config["strings"]["FOOTNOTE"]
    
def format_error_string(errors, config):
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
            
# todo: process comment