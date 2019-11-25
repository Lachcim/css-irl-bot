import logging
import re
import praw
import cssirlbot.submissionhistory
import cssirlbot.validation

def process_submission(submission, config, reply_target=None):
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
        home_subreddit = config["behavior"]["subreddit"]
        foreign = reply_target is not None
        reply_target = reply_target or submission
        external = reply_target.subreddit.display_name != home_subreddit
        
        if result == True and comment_on_valid:
            comment = reply_target.reply(format_title_success_string(config, foreign, external))
        elif result == False and comment_on_invalid:
            comment = reply_target.reply(format_title_error_string(errors, config))
        
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
            
def format_title_success_string(config, foreign, external):
    message = ""
    
    # add message addressed to op or not
    if not foreign:
        message += config["strings"]["VALID_TITLE_MESSAGE"]
    else:
        message += config["strings"]["VALID_TITLE_MESSAGE_FOREIGN"]
    
    # add universal footnote
    message += config["strings"]["FOOTNOTE"]
    
    # if external, add postcard
    if external:
        message += config["strings"]["POSTCARD"]
    
    return message
    
def format_title_error_string(errors, config, foreign, external):
    message = ""
    
    # add message addressed to op or not
    if not foreign:
        message += config["strings"]["INVALID_TITLE_MESSAGE"]
    else:
        message += config["strings"]["INVALID_TITLE_MESSAGE_FOREIGN"]
    
    # list errors
    for error in errors:
        # protection against markdown injection, no way to escape the grave accent
        error["message"] = error["message"].replace("`", "'")
        
        message += config["strings"]["IVALID_CSS_ERROR"].format(**error)
    
    # add universal error tail and footnote
    message += config["strings"]["IVALID_CSS_TAIL"]
    message += config["strings"]["FOOTNOTE"]
    
    # if external, add postcard
    if external:
        message += config["strings"]["POSTCARD"]
    
    return message
            
def process_comment(comment, config, reddit):
    # get config
    home_subreddit = config["behavior"]["subreddit"]
    process_external = config["behavior"]["process_external_mentions"]
    
    # exclude external mentions if configured as such
    if comment.subreddit.display_name != home_subreddit and not process_external:
        logging.info("Ignoring external mention")
        cssirlbot.submissionhistory.mark_as_processed(comment) # prevent reprocessing
        return True
        
    # get command used in mention
    command = get_command(comment.body, config, reddit.user.me().name)
    
    # handle parsing the op
    if command == "parse_op" or (command == "parse_parent" and comment.parent_id.startswith("t3_")):
        # obtain op submission, trim prefix
        op = reddit.submission(id=comment.parent_id[3:])
        
        # don't parse op if already parsed
        if cssirlbot.submissionhistory.is_processed(op):
            logging.info("Mention points to already parsed post")
            # mark comment as handled
            cssirlbot.submissionhistory.mark_as_processed(comment)
            return True
        
        # delegate submission handling to standard function
        result = process_submission(op, config, comment)
        if result:
            # mark comment as handled on success
            cssirlbot.submissionhistory.mark_as_processed(comment)
            
        return result
    
    # todo: process comment
    return True

def get_command(body, config, username):
    # find valid command calls
    expression = re.compile("^/?u/" + username + "/?\s*(\S*)\s*$", re.MULTILINE)
    matches = re.findall(expression, body)
    
    # find first valid command
    for match in matches:
        for command, keywords in config["commands"].items():
            if match in keywords:
                return command
    
    # return none on failure
    return None
