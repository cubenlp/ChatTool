import asyncio
from chattool import Chat, AzureChat
from chattool.const import CHATTOOL_REPO_DIR
test_dir = CHATTOOL_REPO_DIR / 'tests' / 'testfiles'

async def get_res(msg):
    chat = Chat(msg)
    chat.assistant('hi')
    asyncio.sleep(0.1)
    return chat

def test_batch():
    Chat.batch_process_chat(
        [f'hello {i}' for i in range(10)], get_res)
    
    checkpoint = test_dir/'hello'
    Chat.batch_process_chat(
        [f'hello {i}' for i in range(2)], get_res, checkpoint=checkpoint)
    
    Chat.batch_process_chat(
        [f'hello {i}' for i in range(10)], get_res, checkpoint=checkpoint)

    checkpoint.unlink()
    
if __name__ == '__main__':
    test_batch()