# Reddit Steam Support Analysis

A small, read-only, non-commercial personal data-analysis project for examining publicly discussed Steam/Valve support issues.

## Purpose

The project is intended to answer two primary questions from public Reddit discussions:

1. What did the user need support with?
2. Does the subsequent discussion indicate that the problem was resolved?

A later analysis step may use an LLM to classify the text of each conversation. Reddit data will **not** be used to train or fine-tune an AI/ML model.

## Scope

The initial validation run is intentionally limited to 13 manually selected public Reddit threads listed in `sample_urls.txt`.

If Reddit approves Data API access and the validation succeeds, the intended one-time snapshot will cover selected Steam/Valve-related subreddits over a fixed historical period. The collector is read-only: it does not post, comment, vote, message users, moderate communities, or access private data.

## Workflow

```text
Reddit Data API (OAuth)
        |
        v
Python collector
        |
        v
Local JSONL snapshot
        |
        v
LLM classification
        |
        v
Structured analysis
        |
        v
Aggregate statistics
```

The Python collector performs **no semantic classification**. It preserves the public post, public comments, thread relationships, and basic metadata. Whether a post is a support request, what support was needed, and whether the problem was resolved are determined later from the conversation content.

## Privacy and data handling

- The collector is read-only.
- Private messages and private Reddit data are out of scope.
- Reddit usernames are not needed for the analysis. Within each collected thread, authors are represented locally as `OP`, `USER_001`, `USER_002`, etc., so conversational relationships can be preserved without retaining usernames in the analysis dump.
- Raw Reddit data and analysis outputs are local artifacts and are excluded from this repository.
- The project will comply with Reddit's applicable API, deletion, retention, and rate-limit requirements.
- The dataset will not be sold, licensed, published as a dataset, or incorporated into a commercial product.
- Reddit content will not be used to train or fine-tune an AI/ML model.

## Status

**Pre-approval.** This repository documents the proposed implementation for a Reddit Data API access request. The collector must not be run against the Reddit Data API until explicit access approval and OAuth credentials are obtained.

## Authentication

The collector is designed for OAuth authentication using credentials supplied through environment variables. Credentials are never committed to the repository.

Expected environment variables:

```text
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
REDDIT_USERNAME
REDDIT_PASSWORD
```

The authenticated Reddit username is used only for OAuth. It is not written to the output.

## Test run

After approval:

```bash
python -m pip install -r requirements.txt
python collect_threads.py sample_urls.txt steam_support_test_dump.jsonl
```

The initial run retrieves only the URLs in `sample_urls.txt`.

## Dependencies

Python 3.10+ and PRAW, a Python wrapper for Reddit's API.

## License

The source code in this repository is provided for this personal analysis project. Reddit content is not included in the repository and remains subject to Reddit's terms and applicable rights.
