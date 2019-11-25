import logging
import praw
import cssirlbot.submissionhistory
import cssirlbot.validation

# process post submission
def process_submission(submission, config):
    # validate submission
    result, errors = cssirlbot.validation.validate_title(submission.title)
    
    if result == None:
        logging.error("Error while validating")
        return
    
    try:
        # reply to submission
        if result == True and config["behavior"]["comment_on_valid_css"]:
            comment = submission.reply(config["strings"]["VALID_CSS_MESSAGE"] + config["strings"]["FOOTNOTE"])
        elif result == False and config["behavior"]["comment_on_invalid_css"]:
            comment = submission.reply(cssirlbot.validation.format_error_string(errors, config))
        
        # distinguish comment
        if config["behavior"]["distinguish_comments"]:
            comment.mod.distinguish(how="yes", sticky=config["behavior"]["sticky_comments"])
        
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