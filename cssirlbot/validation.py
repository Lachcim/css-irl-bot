import json
import requests

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
    if not is_parse_error(errors):
        return result, errors
        
    # if there was a parse error, retry validation with dummy selector wrapped around
    new_result, new_errors = validate_query(".dummySelector { " + title + " }")
    
    # if new query resulted in a single parse error, return the old error
    if is_parse_error(new_errors):
        return result, errors
    
    # otherwise return the new result
    return new_result, new_errors
    
def is_parse_error(errors):
    # check whether an error list only contains a single parse error
    
    parse_error = False
    non_parse_error = False
    
    for error in errors:
        if "Parse Error." in error["message"]:
            parse_error = True
        else:
            non_parse_error = True
            
    return parse_error and not non_parse_error
