"""
chattool zulip — Zulip CLI helpers

Commands:
    chattool zulip streams     List streams
    chattool zulip topics      List topics in a stream
    chattool zulip topic       Export full topic thread
    chattool zulip messages    Get messages
    chattool zulip profile     Show bot profile
    chattool zulip news        Summarize recent updates
"""

from __future__ import annotations

import json
import time
import datetime
from typing import List, Optional, Dict

import click

from chattool.interaction import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    resolve_command_inputs,
)

from chattool.tools.zulip import ZulipClient
from chattool.config import ZulipConfig
from chattool.llm import Chat


@click.group()
def cli():
    """Zulip tools (read-only)"""
    pass


def _get_client() -> ZulipClient:
    try:
        return ZulipClient()
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


def _parse_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _coerce_int(value: Optional[int], fallback: int, label: str) -> int:
    if value is not None:
        return int(value)
    try:
        return int(fallback)
    except Exception as exc:
        raise click.ClickException(f"Invalid {label} value: {fallback}") from exc


def _clean_text(text: str, max_len: int = 200) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) > max_len:
        return cleaned[: max_len - 1] + "…"
    return cleaned


def _format_ts(ts: int) -> str:
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


ZULIP_STREAM_SCHEMA = CommandSchema(
    name="zulip-stream",
    fields=(CommandField("stream", prompt="stream", required=True),),
)


ZULIP_TOPIC_SCHEMA = CommandSchema(
    name="zulip-topic",
    fields=(
        CommandField("stream", prompt="stream", required=True),
        CommandField("topic_name", prompt="topic", required=True),
    ),
)


def _resolve_stream_id(client: ZulipClient, stream: str) -> Optional[int]:
    if stream.isdigit():
        return int(stream)

    subs = client.list_subscriptions()
    for item in subs:
        if item.get("name") == stream:
            return item.get("stream_id")

    items = client.list_streams(include_public=True)
    for item in items:
        if item.get("name") == stream:
            return item.get("stream_id")

    return None


@cli.command(name="streams")
@click.option(
    "--all", "show_all", is_flag=True, help="Show all accessible public streams"
)
@click.option("--json-output", is_flag=True, help="Output JSON")
def streams(show_all: bool, json_output: bool):
    """List streams (subscribed by default)."""
    client = _get_client()
    if show_all:
        items = client.list_streams(include_public=True)
    else:
        items = client.list_subscriptions()

    if json_output:
        click.echo(json.dumps(items, ensure_ascii=False, indent=2))
        return

    if not items:
        click.echo("No streams found.")
        return

    for item in items:
        name = item.get("name")
        stream_id = item.get("stream_id")
        desc = item.get("description", "")
        click.echo(f"- {name} (id={stream_id})")
        if desc:
            click.echo(f"  {desc}")


@cli.command(name="topics")
@click.option("--stream", required=False, help="Stream name or id")
@click.option("--json-output", is_flag=True, help="Output JSON")
@add_interactive_option
def topics(stream: str, json_output: bool, interactive):
    """List topics for a stream."""
    inputs = resolve_command_inputs(
        schema=ZULIP_STREAM_SCHEMA,
        provided={"stream": stream},
        interactive=interactive,
        usage="Usage: chattool zulip topics --stream TEXT [-i|-I]",
    )
    stream = inputs["stream"]

    client = _get_client()
    stream_id = _resolve_stream_id(client, stream)
    if stream_id is None:
        raise click.ClickException(f"Stream not found: {stream}")

    items = client.list_topics(stream_id)

    if json_output:
        click.echo(json.dumps(items, ensure_ascii=False, indent=2))
        return

    if not items:
        click.echo("No topics found.")
        return

    items = sorted(items, key=lambda x: x.get("max_id") or 0, reverse=True)
    for item in items:
        name = item.get("name")
        max_id = item.get("max_id")
        click.echo(f"- {name} (max_id={max_id})")


@cli.command(name="messages")
@click.option("--anchor", default="newest", help="Message anchor ID or newest/oldest")
@click.option(
    "--before",
    "num_before",
    default=20,
    show_default=True,
    help="Messages before anchor",
)
@click.option(
    "--after", "num_after", default=0, show_default=True, help="Messages after anchor"
)
@click.option("--stream", default=None, help="Stream filter")
@click.option("--topic", default=None, help="Topic filter")
@click.option("--sender", default=None, help="Sender email filter")
@click.option("--search", default=None, help="Search keyword")
@click.option("--json-output", is_flag=True, help="Output JSON")
def messages(anchor, num_before, num_after, stream, topic, sender, search, json_output):
    """Get messages with optional filters."""
    client = _get_client()
    narrow = []
    if stream:
        narrow.append({"operator": "stream", "operand": stream})
    if topic:
        narrow.append({"operator": "topic", "operand": topic})
    if sender:
        narrow.append({"operator": "sender", "operand": sender})
    if search:
        narrow.append({"operator": "search", "operand": search})

    items = client.get_messages(
        anchor=anchor,
        num_before=num_before,
        num_after=num_after,
        narrow=narrow if narrow else None,
    )

    if json_output:
        click.echo(json.dumps(items, ensure_ascii=False, indent=2))
        return

    if not items:
        click.echo("No messages found.")
        return

    for msg in items:
        ts = _format_ts(msg.get("timestamp", 0))
        stream_name = msg.get("display_recipient") or msg.get("stream")
        topic_name = msg.get("subject")
        sender_name = msg.get("sender_full_name")
        content = _clean_text(msg.get("content", ""), max_len=160)
        click.echo(f"[{ts}] {stream_name} > {topic_name} | {sender_name}")
        click.echo(f"  {content}")


@cli.command(name="topic")
@click.option("--stream", required=False, help="Stream name or id")
@click.option("--topic", "topic_name", required=False, help="Topic name")
@click.option("--limit", type=int, default=None, help="Limit to latest N messages")
@click.option("--json-output", is_flag=True, help="Output JSON")
@add_interactive_option
def topic(
    stream: str, topic_name: str, limit: Optional[int], json_output: bool, interactive
):
    """Export full topic thread."""
    inputs = resolve_command_inputs(
        schema=ZULIP_TOPIC_SCHEMA,
        provided={"stream": stream, "topic_name": topic_name},
        interactive=interactive,
        usage="Usage: chattool zulip topic --stream TEXT --topic TEXT [-i|-I]",
    )
    stream = inputs["stream"]
    topic_name = inputs["topic_name"]

    client = _get_client()
    items = client.get_topic_messages(stream, topic_name)

    if limit:
        items = items[-limit:]

    if json_output:
        click.echo(json.dumps(items, ensure_ascii=False, indent=2))
        return

    if not items:
        click.echo("No messages found.")
        return

    click.echo(f"# {stream} / {topic_name}")
    click.echo("")
    click.echo(f"Messages: {len(items)}")
    click.echo("")
    for msg in items:
        ts = _format_ts(msg.get("timestamp", 0))
        sender_name = msg.get("sender_full_name") or "unknown"
        content = msg.get("content", "")
        click.echo(f"- {ts} — {sender_name}: {content}")


@cli.command(name="profile")
def profile():
    """Show current bot profile (credentials check)."""
    client = _get_client()
    data = client.get_profile()
    click.echo(json.dumps(data, ensure_ascii=False, indent=2))


def _render_fallback_summary(messages: List[Dict[str, Any]]) -> str:
    if not messages:
        return "No messages matched the criteria."

    topic_counter: Dict[str, int] = {}
    for msg in messages:
        stream_name = msg.get("display_recipient") or msg.get("stream") or "unknown"
        topic_name = msg.get("subject") or "unknown"
        key = f"{stream_name} / {topic_name}"
        topic_counter[key] = topic_counter.get(key, 0) + 1

    top_topics = sorted(topic_counter.items(), key=lambda x: x[1], reverse=True)[:10]
    lines = ["Rule-based summary (LLM unavailable).", "", "Hot topics:"]
    for name, count in top_topics:
        lines.append(f"- {name} ({count})")
    return "\n".join(lines)


def _render_news_markdown(
    messages: List[Dict[str, Any]],
    summary: str,
    streams: List[str],
    topics: List[str],
    since_hours: int,
    since_ts: int,
    output_time: datetime.datetime,
) -> str:
    header = [
        f"# Zulip News ({output_time.strftime('%Y-%m-%d %H:%M')})",
        "",
        f"- Window: last {since_hours} hours ({_format_ts(since_ts)} ~ {output_time.strftime('%Y-%m-%d %H:%M:%S')})",
        f"- Streams: {', '.join(streams) if streams else 'ALL'}",
        f"- Topics: {', '.join(topics) if topics else 'ALL'}",
        f"- Messages: {len(messages)}",
        "",
        "## Summary",
        summary.strip() if summary else "(no summary)",
        "",
    ]

    topic_counter: Dict[str, int] = {}
    for msg in messages:
        stream_name = msg.get("display_recipient") or msg.get("stream") or "unknown"
        topic_name = msg.get("subject") or "unknown"
        key = f"{stream_name} / {topic_name}"
        topic_counter[key] = topic_counter.get(key, 0) + 1
    top_topics = sorted(topic_counter.items(), key=lambda x: x[1], reverse=True)[:10]

    header.append("## Hot Topics")
    if top_topics:
        for name, count in top_topics:
            header.append(f"- {name} ({count})")
    else:
        header.append("- (none)")
    header.append("")

    header.append("## Selected Messages")
    if not messages:
        header.append("- (none)")
        return "\n".join(header)

    for msg in messages[: min(30, len(messages))]:
        ts = _format_ts(msg.get("timestamp", 0))
        stream_name = msg.get("display_recipient") or msg.get("stream") or "unknown"
        topic_name = msg.get("subject") or "unknown"
        sender_name = msg.get("sender_full_name") or "unknown"
        content = _clean_text(msg.get("content", ""), max_len=180)
        header.append(
            f"- [{ts}] **{stream_name}** / *{topic_name}* — {sender_name}: {content}"
        )
    return "\n".join(header)


@cli.command(name="news")
@click.option("--stream", "streams", multiple=True, help="Specify stream (repeatable)")
@click.option("--topic", "topics", multiple=True, help="Specify topic (repeatable)")
@click.option(
    "--since-hours", type=int, default=None, help="Look back N hours (default 24)"
)
@click.option("--per-stream", type=int, default=None, help="Per-stream fetch limit")
@click.option("--limit", type=int, default=None, help="Global message cap (latest)")
@click.option("--output", default=None, help="Output file path (Markdown)")
@click.option("--model", default=None, help="LLM model override")
@click.option(
    "--max-tokens", type=int, default=800, show_default=True, help="Summary max tokens"
)
@click.option(
    "--temperature",
    type=float,
    default=0.2,
    show_default=True,
    help="Summary temperature",
)
def news(
    streams,
    topics,
    since_hours,
    per_stream,
    limit,
    output,
    model,
    max_tokens,
    temperature,
):
    """Summarize recent updates (console + Markdown file)."""
    client = _get_client()

    cfg_streams = _parse_csv(ZulipConfig.ZULIP_NEWS_STREAMS.value)
    cfg_topics = _parse_csv(ZulipConfig.ZULIP_NEWS_TOPICS.value)
    streams = list(streams) or cfg_streams
    topics = list(topics) or cfg_topics

    since_hours = _coerce_int(
        since_hours,
        ZulipConfig.ZULIP_NEWS_SINCE_HOURS.value or 24,
        "since-hours",
    )
    per_stream = _coerce_int(
        per_stream,
        ZulipConfig.ZULIP_NEWS_PER_STREAM.value or 200,
        "per-stream",
    )

    if not streams:
        subs = client.list_subscriptions()
        streams = [item.get("name") for item in subs if item.get("name")]
        if not streams:
            public_streams = client.list_streams(include_public=False)
            streams = [item.get("name") for item in public_streams if item.get("name")]

    if not streams:
        raise click.ClickException(
            "No streams available. Set ZULIP_NEWS_STREAMS or pass --stream."
        )

    now = int(time.time())
    since_ts = now - since_hours * 3600

    all_messages: List[Dict[str, Any]] = []
    for stream in streams:
        narrow = [{"operator": "stream", "operand": stream}]
        msgs = client.get_messages(
            anchor="newest",
            num_before=per_stream,
            num_after=0,
            narrow=narrow,
        )
        for msg in msgs:
            ts = msg.get("timestamp", 0)
            if ts < since_ts:
                continue
            if topics:
                if msg.get("subject") not in topics:
                    continue
            all_messages.append(msg)

    if not all_messages:
        summary = "No messages matched the criteria."
        output_time = datetime.datetime.now()
        markdown = _render_news_markdown(
            messages=[],
            summary=summary,
            streams=streams,
            topics=topics,
            since_hours=since_hours,
            since_ts=since_ts,
            output_time=output_time,
        )
        _write_news_output(markdown, output, output_time)
        click.echo(markdown)
        return

    all_messages.sort(key=lambda x: x.get("timestamp", 0))
    if limit:
        all_messages = all_messages[-limit:]

    summary = ""
    try:
        summary = _llm_summarize(
            all_messages, streams, topics, since_hours, model, max_tokens, temperature
        )
    except Exception as exc:
        summary = _render_fallback_summary(all_messages)
        click.echo(
            f"LLM summary failed, fell back to rule-based summary: {exc}", err=True
        )

    output_time = datetime.datetime.now()
    markdown = _render_news_markdown(
        messages=list(reversed(all_messages))
        if len(all_messages) > 30
        else all_messages,
        summary=summary,
        streams=streams,
        topics=topics,
        since_hours=since_hours,
        since_ts=since_ts,
        output_time=output_time,
    )
    _write_news_output(markdown, output, output_time)
    click.echo(markdown)


def _llm_summarize(
    messages: List[Dict[str, Any]],
    streams: List[str],
    topics: List[str],
    since_hours: int,
    model: Optional[str],
    max_tokens: int,
    temperature: float,
) -> str:
    sample = messages[-min(len(messages), 200) :]
    lines = []
    for msg in sample:
        ts = _format_ts(msg.get("timestamp", 0))
        stream_name = msg.get("display_recipient") or msg.get("stream") or "unknown"
        topic_name = msg.get("subject") or "unknown"
        sender_name = msg.get("sender_full_name") or "unknown"
        content = _clean_text(msg.get("content", ""), max_len=240)
        lines.append(
            f"- [{ts}] {stream_name} / {topic_name} | {sender_name}: {content}"
        )

    system_prompt = (
        "You are a community editor. Summarize the messages concisely and accurately. "
        "Do not invent details. Output Markdown with 3-6 bullet points, each no more than two sentences."
    )
    user_prompt = "\n".join(
        [
            f"Time window: last {since_hours} hours",
            f"Streams: {', '.join(streams) if streams else 'ALL'}",
            f"Topics: {', '.join(topics) if topics else 'ALL'}",
            "",
            "Messages (chronological):",
            *lines,
        ]
    )

    chat = Chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    resp = chat.get_response(
        max_tokens=max_tokens, temperature=temperature, model=model
    )
    return (resp.content or "").strip()


def _write_news_output(
    markdown: str, output: Optional[str], output_time: datetime.datetime
) -> str:
    if output:
        output_path = output
    else:
        output_path = f"zulip-news-{output_time.strftime('%Y%m%d')}.md"
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    click.echo(f"Saved to {output_path}")
    return output_path
