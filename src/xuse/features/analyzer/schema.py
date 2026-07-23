def structured_analysis_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "relevance": {"type": "number"},
            "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
            "recommended_action": {"type": "string", "enum": ["quote_tweet", "retweet", "repost", "like"]},
            "confidence": {"type": "number"},
            "is_thread": {"type": "boolean"},
            "topics": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["relevance", "sentiment", "recommended_action", "confidence"],
    }

