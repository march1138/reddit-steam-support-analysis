#!/usr/bin/env python3
"""Read-only Reddit thread collector.

PRE-APPROVAL STATUS:
Do not run this script against Reddit until Reddit has explicitly approved
Data API access for this project and OAuth credentials have been issued.

The collector intentionally performs no semantic classification. It retrieves
public post/comment content and basic metadata and writes one JSON object per
thread to a local JSONL file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import praw
from praw.models import MoreComments


APP_ID = "reddit-steam-support-analysis"
APP_VERSION = "0.1.0"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_reddit() -> praw.Reddit:
    username = require_env("REDDIT_USERNAME")
    return praw.Reddit(
        client_id=require_env("REDDIT_CLIENT_ID"),
        client_secret=require_env("REDDIT_CLIENT_SECRET"),
        username=username,
        password=require_env("REDDIT_PASSWORD"),
        user_agent=f"python:{APP_ID}:{APP_VERSION} (by /u/{username})",
        check_for_async=False,
    )


def read_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def utc_iso(timestamp: float | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def stable_thread_alias(author_name: str | None, op_name: str | None,
                        aliases: dict[str, str]) -> str:
    """Return a thread-local pseudonym without storing the Reddit username."""
    if author_name is None:
        return "DELETED_USER"
    if op_name is not None and author_name == op_name:
        return "OP"
    if author_name not in aliases:
        aliases[author_name] = f"USER_{len(aliases) + 1:03d}"
    return aliases[author_name]


def comment_record(comment: Any, op_name: str | None,
                   aliases: dict[str, str]) -> dict[str, Any]:
    author_name = comment.author.name if comment.author else None
    return {
        "comment_id": comment.id,
        "parent_id": comment.parent_id,
        "created_utc": utc_iso(getattr(comment, "created_utc", None)),
        "body": comment.body,
        "score": comment.score,
        "depth": comment.depth,
        "author_role": stable_thread_alias(author_name, op_name, aliases),
        "is_submitter": bool(getattr(comment, "is_submitter", False)),
        "edited": comment.edited if comment.edited else False,
        "distinguished": comment.distinguished,
        "stickied": bool(comment.stickied),
    }


def collect_submission(reddit: praw.Reddit, url: str) -> dict[str, Any]:
    submission = reddit.submission(url=url)

    # Ask PRAW to expand "MoreComments" placeholders so the dump contains the
    # available public comment tree rather than only the initially returned set.
    submission.comments.replace_more(limit=None)

    op_name = submission.author.name if submission.author else None
    aliases: dict[str, str] = {}

    comments: list[dict[str, Any]] = []
    for comment in submission.comments.list():
        if isinstance(comment, MoreComments):
            continue
        comments.append(comment_record(comment, op_name, aliases))

    return {
        "schema_version": 1,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": url,
        "post_id": submission.id,
        "subreddit": submission.subreddit.display_name,
        "created_utc": utc_iso(submission.created_utc),
        "title": submission.title,
        "body": submission.selftext,
        "flair": submission.link_flair_text,
        "score": submission.score,
        "upvote_ratio": submission.upvote_ratio,
        "num_comments_reported": submission.num_comments,
        "permalink": f"https://www.reddit.com{submission.permalink}",
        "edited": submission.edited if submission.edited else False,
        "locked": bool(submission.locked),
        "stickied": bool(submission.stickied),
        "author_role": stable_thread_alias(op_name, op_name, aliases),
        "comments_collected": len(comments),
        "comments": comments,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect specified public Reddit threads to local JSONL."
    )
    parser.add_argument("url_file", type=Path, help="Text file containing Reddit URLs")
    parser.add_argument("output_file", type=Path, help="Local JSONL output path")
    args = parser.parse_args()

    urls = read_urls(args.url_file)
    if not urls:
        print("No URLs found.", file=sys.stderr)
        return 2

    # Guard against accidentally committing output under a misleading extension.
    if args.output_file.suffix.lower() != ".jsonl":
        print("Output file must use the .jsonl extension.", file=sys.stderr)
        return 2

    reddit = build_reddit()

    print(f"Preparing to collect {len(urls)} explicitly listed thread(s).")
    with args.output_file.open("w", encoding="utf-8") as handle:
        for index, url in enumerate(urls, start=1):
            try:
                record = collect_submission(reddit, url)
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(
                    f"[{index}/{len(urls)}] {record['post_id']} "
                    f"r/{record['subreddit']} - {record['comments_collected']} comments"
                )
            except Exception as exc:
                # Keep failures visible without fabricating a partial thread record.
                digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
                print(f"[{index}/{len(urls)}] ERROR {digest}: {exc}", file=sys.stderr)

    print(f"Finished. Local output: {args.output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
