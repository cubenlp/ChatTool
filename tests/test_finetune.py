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
    # upload files
    ft = FineTune()
    ft.training_file(trainfile)
    ft.validation_file(validfile)
    # get file list
    files = ft.list_files()
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
    jobs = ft.list_jobs(limit=1)
    jobid = jobs[0]['id']
    # TODO: create job/cancel job/delete job
    # retrieve job
    ft.retrieve_job(jobid)
    # list events
    ft.list_events(jobid)
    ft.list_events(jobid, limit=20)
    # default repl
    print(ft)
    # get model list
    models = ft.list_models()
    # delete files
    for file in files:
        if file['filename'] in [trainfile, validfile] and \
            file['status'] == 'processed':
            ft.delete_file(file['id'])
    
def test_finetune_initialize():
    ft = FineTune(api_key="sk-xxx", base_url="https://api.openai.com")
    ft = FineTune(model="gpt-3.5-turbo-0301", modelid="xxx", jobid="xxx")
    print(ft.jobid, ft.modelid)
    ft = FineTune(trainingid="xxx", validationid="xxx")
    print(ft.trainingid, ft.validationid)
    ft.api_key = "sk-xxx"
    ft.base_url = "https://api.openai.com"
    ft.model = "gpt-3.5-turbo-0301"
    ft.jobid = "xxx"
