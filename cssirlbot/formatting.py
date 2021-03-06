def format_title_success_string(config, foreign, author, external):
    message = ""
    
    # add message addressed to op or not
    if not foreign:
        message += config["strings"]["VALID_TITLE_MESSAGE"]
    else:
        message += config["strings"]["VALID_TITLE_MESSAGE_FOREIGN"].format(author=author)
    
    # add universal footnote
    message += config["strings"]["FOOTNOTE"]
    
    # if external, add postcard
    if external:
        message += config["strings"]["POSTCARD"]
    
    return message
    
def format_title_error_string(errors, config, foreign, author, external):
    message = ""
    
    # add message addressed to op or not
    if not foreign:
        message += config["strings"]["INVALID_TITLE_MESSAGE_HEAD"]
    else:
        message += config["strings"]["INVALID_TITLE_MESSAGE_HEAD_FOREIGN"].format(author=author)
    
    # list errors
    for error in errors:
        # protection against markdown injection, no way to escape the grave accent
        error["message"] = error["message"].replace("`", "'")
        
        message += config["strings"]["INVALID_CSS_ERROR"].format(**error)
    
    # add universal error tail and footnote
    message += config["strings"]["INVALID_CSS_TAIL"]
    message += config["strings"]["FOOTNOTE"]
    
    # if external, add postcard
    if external:
        message += config["strings"]["POSTCARD"]
    
    return message

def format_comment_success_string(source, css, config, foreign, author, external):
    message = ""
    
    # state the source
    message += config["strings"]["CSS_SOURCE_" + source.upper()]
    
    # print the source
    if source != "body":
        message += ("    " + css).replace("\n", "\n    ") + "\n"
    
    # add message addressed to op or not
    if not foreign:
        message += config["strings"]["VALID_COMMENT_MESSAGE"]
    else:
        message += config["strings"]["VALID_COMMENT_MESSAGE_FOREIGN"].format(author=author)
        
    # add universal footnote
    message += config["strings"]["FOOTNOTE"]
    
    # if external, add postcard
    if external:
        message += config["strings"]["POSTCARD"]
    
    return message

def format_comment_error_string(source, css, errors, config, foreign, author, external):
    message = ""
    
    # state the source
    message += config["strings"]["CSS_SOURCE_" + source.upper()]
    
    # print the source
    if source != "body":
        message += ("    " + css).replace("\n", "\n    ") + "\n"
    
    # add message addressed to op or not
    if not foreign:
        message += config["strings"]["INVALID_COMMENT_MESSAGE_HEAD"]
    else:
        message += config["strings"]["INVALID_COMMENT_MESSAGE_HEAD_FOREIGN"].format(author=author)
        
    # list errors
    for error in errors:
        # protection against markdown injection, no way to escape the grave accent
        error["message"] = error["message"].replace("`", "'")
        
        message += config["strings"]["INVALID_CSS_ERROR"].format(**error)
    
    # add universal error tail and footnote
    message += config["strings"]["INVALID_CSS_TAIL"]
    message += config["strings"]["FOOTNOTE"]
    
    # if external, add postcard
    if external:
        message += config["strings"]["POSTCARD"]
    
    return message
