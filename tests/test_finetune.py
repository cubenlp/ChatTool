from chattool.finetune import FineTune
from chattool import Chat
import time

def test_finetune():
    # create test files
    chat = Chat("hello")
    chat.assistant("Hi, how can I help you?")
    trainfile, validfile = "githubtest_training.jsonl", "githubtest_validation.jsonl"
    chat.savewithmsg(trainfile, mode='w')
    chat.clear()
    chat.user("hi")
    chat.assistant("Hi, how can I help you?")
    chat.savewithmsg(validfile, mode='w')
    assert True
    # upload files
    ft = FineTune()
    ft.training_file(trainfile)
    ft.validation_file(validfile)
    assert True
    # get file list
    files = ft.list_files()
    assert True
    # read file content
    msgs = ft.file_content(ft.validationid)
    assert len(msgs) == 1
    assert msgs[0] == {
        "messages":[
            {"role": "user", "content": "hi"}, 
            {"role": "assistant", "content": "Hi, how can I help you?"}
    ]}
    # get job list
    jobs = ft.list_jobs()
    jobid = jobs[0]['id']
    assert True
    # TODO: create job/cancel job/delete job
    # retrieve job
    ft.retrieve_job(jobid)
    assert True
    # list events
    events = ft.list_events(jobid)
    assert True
    print(ft)
    # delete files
    for file in files:
        if file['filename'] in [trainfile, validfile] and \
            file['status'] == 'processed':
            ft.delete_file(file['id'])
    assert True
    
    