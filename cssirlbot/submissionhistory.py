import os.path

# get processed submissions
processed_submissions = []
if os.path.isfile("processedsubmissions.txt"):
    with open("processedsubmissions.txt", "r") as file:
        for line in file:
            processed_submissions.append(line[:-1])

# mark processed submissions as such
def mark_as_processed(submission):
    # prevent duplicates
    if submission.id in processed_submissions:
        return
    
    # add to list
    processed_submissions.append(submission.id)
    
    # add to file
    with open("processedsubmissions.txt", "a") as file:
        file.write(submission.id + "\n")
        
# check if submission has been processed
def is_processed(submission):
    return submission.id in processed_submissions