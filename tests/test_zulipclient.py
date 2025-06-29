from chattool.tools import ZulipClient
from tests.const import logger
import pytest
import asyncio


def test_zulip_client(zulip_client:ZulipClient):
    """测试ZulipClient的基本功能"""
    # get channels
    channels = zulip_client.get_channels()
    for channel in channels[:3]:
        logger.debug(f"Channel: {channel}")
    channel = channels[0]
    channel_id = channel['stream_id']
    logger.debug(channel)

    # get topic
    topics = zulip_client.get_topics(channel_id)
    print(topics)
    topic = topics[0]
    topic_name = topic['name']
    logger.debug(f"Topic: {topic_name}")

    # get topic history
    messages = zulip_client.get_topic_history(channel_id, topic_name, batch_size=5)
    logger.debug(len(messages))
    for msg in messages[:5]:
        print(msg['content'])
        print('-'*100)


# @pytest.mark.asyncio
# async def test_async_zulip_client(zulip_client:ZulipClient):
#     """测试ZulipClient的异步功能"""
#     # 获取频道
#     channels = await zulip_client.get_channels_async()
#     assert channels, "未能获取到频道列表"
    
#     # 获取第一个频道的ID
#     channel_id = channels[0]['stream_id']
    
#     # 获取话题
#     topics = await zulip_client.get_topics_async(channel_id)
#     assert topics, "未能获取到话题列表"
    
#     # 获取第一个话题的名称
#     topic_name = topics[0]['name']
    
#     # 获取话题历史
#     messages = await zulip_client.get_topic_history_async(channel_id, topic_name, batch_size=5)
#     assert messages, "未能获取到话题历史消息"
    
#     logger.debug(f"获取到 {len(messages)} 条消息")
#     for msg in messages[:5]:
#         logger.debug(f"消息内容: {msg['content'][:100]}...")