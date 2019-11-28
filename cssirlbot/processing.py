import logging
import re
import traceback
import mistune
import praw
import cssirlbot.submissionhistory
import cssirlbot.validation
import cssirlbot.formatting

def process_submission(submission, config, reply_target=None):
    # get config
    comment_on_valid = config["behavior"]["comment_on_valid_css"]
    comment_on_invalid = config["behavior"]["comment_on_invalid_css"]
    distinguish_comments = config["behavior"]["distinguish_comments"]
    sticky_comments = config["behavior"]["sticky_comments"]
    
    # validate submission
    result, errors = cssirlbot.validation.validate_text(submission.title)
    
    # signal failure if needed
    if result == None:
        logging.error("Error while validating")
        return False
    
    try:
        # reply to submission
        home_subreddit = config["behavior"]["subreddit"]
        foreign = reply_target is not None
        reply_target = reply_target or submission
        author = submission.author.name
        external = reply_target.subreddit.display_name != home_subreddit
        
        if result == True and (comment_on_valid or foreign):
            comment = reply_target.reply(cssirlbot.formatting.format_title_success_string(config, foreign, author, external))
        elif result == False and (comment_on_invalid or foreign):
            comment = reply_target.reply(cssirlbot.formatting.format_title_error_string(errors, config, foreign, author, external))
        
        # distinguish comment
        if distinguish_comments:
            try:
                comment.mod.distinguish(how="yes", sticky=sticky_comments)
            except:
                pass
        
        # mark submission as processed
        cssirlbot.submissionhistory.mark_as_processed(submission)
        
        logging.info("Processed!")
        return True
    except praw.exceptions.APIException as e:
        return handle_error(submission, e)
            
def handle_error(submission, e):
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

def process_comment(comment, config, reddit):
    # get config
    home_subreddit = config["behavior"]["subreddit"]
    process_external = config["behavior"]["process_external_mentions"]
    distinguish_comments = config["behavior"]["distinguish_comments"]
    
    # exclude external mentions if configured as such
    if comment.subreddit.display_name != home_subreddit and not process_external:
        logging.info("Ignoring external mention")
        cssirlbot.submissionhistory.mark_as_processed(comment) # prevent reprocessing
        return True
        
    # get command used in mention
    command = get_command(comment.body, config, reddit.user.me().name)
    
    # handle invalid commands
    if not command:
        logging.info("Mention doesn't contain a valid command")
        # mark comment as handled
        cssirlbot.submissionhistory.mark_as_processed(comment)
        return True
    
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
    
    # find css and validate it
    css_origin = comment if command == "parse_this" else reddit.comment(id=comment.parent_id[3:])
    css, css_source = find_css(css_origin.body)
    result, errors = cssirlbot.validation.validate_text(css)
    
    # signal failure if needed
    if result == None:
        logging.error("Error while validating")
        return False
    
    try:
        # reply to comment
        home_subreddit = config["behavior"]["subreddit"]
        foreign = command == "parse_parent"
        author = css_origin.author.name
        external = comment.subreddit.display_name != home_subreddit
        
        if result == True:
            new_comment = comment.reply(cssirlbot.formatting.format_comment_success_string(css_source, css, config, foreign, author, external))
        else:
            new_comment = comment.reply(cssirlbot.formatting.format_comment_error_string(css_source, css, errors, config, foreign, author, external))
        
        # distinguish comment
        if distinguish_comments:
            try:
                new_comment.mod.distinguish(how="yes")
            except:
                pass
        
        # mark comments as processed
        cssirlbot.submissionhistory.mark_as_processed(comment)
        if foreign:
            cssirlbot.submissionhistory.mark_as_processed(css_origin)
        
        logging.info("Processed!")
        return True
    except praw.exceptions.APIException as e:
        return handle_error(comment, e)

def get_command(body, config, username):
    # find valid command calls
    expression = re.compile("^/?u/" + username + "/?\s*(\S*)\s*$", re.MULTILINE | re.IGNORECASE)
    matches = re.findall(expression, body)
    
    # find first valid command
    for match in matches:
        for command, keywords in config["commands"].items():
            if match.lower() in keywords:
                return command
    
    # return none on failure
    return None

def find_css(body):
    # parse markdown
    md = mistune.create_markdown()
    # alternative algorithm: disable fenced code
    # see https://github.com/Lachcim/css-irl-bot/issues/5 for discussion
    # md.block.rules.remove("fenced_code")
    html = md(body)
    
    # it is known that when one parses html with regex, zalgo sings the song
    # that ends the world. in this case, however, the html produced by mistune
    # can be assumed to be regular and therefore parseable using regex.
    
    # find code blocks
    # expression = re.compile("<pre><code>(.*?)</code></pre>", re.DOTALL)
    expression = re.compile("<pre><code[^>]*>(.*?)</code></pre>", re.DOTALL)
    css = "".join(re.findall(expression, html))
    if css:
        return css, "block"
    
    # if the above failed, find inline code
    expression = re.compile("<code>(.*?)</code>", re.DOTALL)
    css = "\n".join(re.findall(expression, html))
    if css:
        return css, "inline"
        
    # if all failed, parse the entire comment
    return body, "body"
