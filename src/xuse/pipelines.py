"""Canonical pipeline names shared by the CLI and the MCP server.

``x-use run --pipeline`` and the MCP ``run_cycle`` tool both resolve names
through this mapping, so the two surfaces can never drift apart. Keys are the
public names (documented in README.md); values are the ActionConfig
enable-flag that gates the pipeline in the orchestrator.
"""

PIPELINE_FLAGS = {
    "competitor_reposts": "enable_competitor_reposts",
    "keyword_replies": "enable_keyword_replies",
    "keyword_retweets": "enable_keyword_retweets",
    "likes": "enable_liking_tweets",
    "content_curation": "enable_content_curation_posts",
    "community_engagement": "enable_community_engagement",
}

ALL_PIPELINE_ENABLE_FLAGS = list(PIPELINE_FLAGS.values())
