from typing import List, Optional, Union, Dict
from fastmcp import FastMCP
from chattool.tools.zulip import ZulipClient

def list_streams(include_public: bool = True) -> List[Dict]:
    """
    List subscribed (and optionally all public) streams in Zulip.
    """
    client = ZulipClient()
    return client.list_streams(include_public=include_public)

def get_messages(
    anchor: Union[int, str] = "newest", 
    num_before: int = 20, 
    num_after: int = 0,
    stream: Optional[str] = None,
    topic: Optional[str] = None,
    sender: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict]:
    """
    Get messages from Zulip with filtering.
    
    Args:
        anchor: Message ID to start from, or "newest", "oldest"
        num_before: Number of messages before anchor
        num_after: Number of messages after anchor
        stream: Filter by stream name
        topic: Filter by topic name
        sender: Filter by sender email
        search: Filter by search keyword
    """
    client = ZulipClient()
    narrow = []
    if stream:
        narrow.append({"operator": "stream", "operand": stream})
    if topic:
        narrow.append({"operator": "topic", "operand": topic})
    if sender:
        narrow.append({"operator": "sender", "operand": sender})
    if search:
        narrow.append({"operator": "search", "operand": search})
        
    return client.get_messages(
        anchor=anchor, 
        num_before=num_before, 
        num_after=num_after,
        narrow=narrow if narrow else None
    )

def send_message(
    to: Union[str, List[int]], 
    content: str, 
    type: str = "stream", 
    topic: Optional[str] = None
) -> int:
    """
    Send a message to a stream or private user.
    
    Args:
        to: Stream name (str) or list of user IDs (List[int]) or email (str for private)
        content: Message content (Markdown)
        type: "stream" or "private"
        topic: Topic name (required for stream messages)
        
    Returns:
        Message ID
    """
    client = ZulipClient()
    result = client.send_message(to=to, content=content, type=type, topic=topic)
    return result.get("id")

def react(
    message_id: int, 
    emoji_name: str, 
    emoji_code: Optional[str] = None, 
    reaction_type: str = "unicode"
) -> bool:
    """
    Add an emoji reaction to a message.
    
    Args:
        message_id: The ID of the message to react to
        emoji_name: The name of the emoji (e.g. "thumbs_up")
        emoji_code: Optional emoji code
        reaction_type: "unicode", "realm_emoji", or "zulip_extra_emoji"
    """
    client = ZulipClient()
    result = client.react_to_message(message_id, emoji_name, reaction_type=reaction_type)
    return result.get("result") == "success"

def upload_file(file_path: str) -> str:
    """
    Upload a file to Zulip.
    
    Args:
        file_path: Absolute path to the file to upload
        
    Returns:
        The URI of the uploaded file
    """
    client = ZulipClient()
    return client.upload_file(file_path)

def register(mcp: FastMCP):
    """Register Zulip tools with the MCP server."""
    mcp.tool(name="zulip_list_streams", tags=["zulip", "read"])(list_streams)
    mcp.tool(name="zulip_get_messages", tags=["zulip", "read"])(get_messages)
    mcp.tool(name="zulip_send_message", tags=["zulip", "write"])(send_message)
    mcp.tool(name="zulip_react", tags=["zulip", "write"])(react)
    mcp.tool(name="zulip_upload_file", tags=["zulip", "write"])(upload_file)
