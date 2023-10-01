import os, responses
from chattool import Chat, load_chats, process_chats, api_key
testpath = 'tests/testfiles/'

def test_with_checkpoint():
    # save chats without chatid
    chat = Chat()
    checkpath = testpath + "tmp.jsonl"
    chat.save(checkpath, mode="w")
    chat = Chat("hello!")
    chat.save(checkpath) # append
    chat.assistant("你好, how can I assist you today?")
    chat.save(checkpath) # append
    ## load chats
    chats = load_chats(checkpath)
    chat_logs = [
        [],
        [{"role": "user", "content": "hello!"}],
        [{"role": "user", "content": "hello!"}, {"role": "assistant", "content": "你好, how can I assist you today?"}],
    ]
    assert chats == [Chat(log) for log in chat_logs]

    # save chats with chatid
    chat = Chat()
    checkpath = testpath + "tmp_withid.jsonl"
    chat.savewithid(checkpath, mode="w", chatid=0)
    chat = Chat("hello!")
    chat.savewithid(checkpath, chatid=3)
    chat.assistant("你好, how can I assist you today?")
    chat.savewithid(checkpath, chatid=2)
    ## load chats
    chats = load_chats(checkpath, withid=True)
    chat_logs = [
        [],
        None,
        [{"role": "user", "content": "hello!"}, {"role": "assistant", "content": "你好, how can I assist you today?"}],
        [{"role": "user", "content": "hello!"}],
    ]
    assert chats == [Chat(log) if log is not None else None for log in chat_logs]

def test_process_chats():
    def msg2chat(msg):
        chat = Chat()
        chat.system("You are a helpful translator for numbers.")
        chat.user(f"Please translate the digit to Roman numerals: {msg}")
        # chat.getresponse()
        chat.assistant("III")
        return chat
    checkpath = testpath + "tmp_process.jsonl"
    # process part of the data
    msgs = [str(i) for i in range(6)]
    chats = process_chats(msgs[:3], msg2chat, checkpath, clearfile=True)
    for chat in chats:
        print(chat[-1])
    assert len(chats) == 3
    assert all([len(chat) == 3 for chat in chats])
    # continue processing the rest of the data
    continue_chats = process_chats(msgs, msg2chat, checkpath)
    assert len(continue_chats) == 6
    assert all(c1 == c2 for c1, c2 in zip(chats, continue_chats[:3]))
    assert all([len(chat) == 3 for chat in continue_chats])