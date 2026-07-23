from typing import List


def build_thread_prompt(tweet_text: str) -> str:
    return (
        "Analyze the following tweet text to determine if it is part of a thread or a standalone tweet.\n"
        "A tweet is part of a thread if it explicitly indicates continuation (e.g., \"(1/n)\", \"thread below\", \"🧵\"), "
        "or if its content strongly implies it's one piece of a multi-part discussion.\n"
        "Consider common thread indicators.\n\n"
        f"Tweet text:\n\"{tweet_text}\"\n\n"
        "Based on this text, is this tweet likely part of a thread?\n"
        "Respond with only \"true\" or \"false\".\n"
    )


def build_relevance_prompt(tweet_text: str, keywords: List[str]) -> str:
    return (
        "Rate from 0.0 to 1.0 how relevant the tweet is to these keywords.\n"
        f"Tweet: {tweet_text}\nKeywords: {', '.join(keywords)}\n"
        "Only return a number between 0.0 and 1.0."
    )


def build_sentiment_prompt(tweet_text: str) -> str:
    return (
        "Classify the sentiment of the tweet as 'positive', 'neutral', or 'negative'. "
        "Only return one of those words.\n"
        f"Tweet: {tweet_text}\n"
    )

