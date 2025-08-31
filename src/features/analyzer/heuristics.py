from typing import List


POSITIVE_WORDS = ["great", "good", "love", "amazing", "awesome", "excited"]
NEGATIVE_WORDS = ["bad", "terrible", "hate", "awful", "angry", "worse"]


def keyword_relevance_score(text: str, keywords: List[str]) -> float:
    if not text:
        return 0.0
    if not keywords:
        return 0.5
    t = text.lower()
    kws = [k.lower() for k in keywords]
    hits = sum(1 for k in kws if k in t)
    return min(hits / max(1, len(kws)), 1.0)


def heuristic_sentiment(text: str) -> str:
    if not text:
        return "neutral"
    t = text.lower()
    if any(w in t for w in POSITIVE_WORDS):
        return "positive"
    if any(w in t for w in NEGATIVE_WORDS):
        return "negative"
    return "neutral"

