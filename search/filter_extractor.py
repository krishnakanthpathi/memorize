import re
from typing import List, Tuple

# Common English stop words to filter out
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then",
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who",
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}


def extract_keywords_and_snippet(content: str, max_keywords: int = 10) -> Tuple[str, List[str]]:
    """
    Strips Markdown formatting, filters out stop words, and extracts:
    1. A clean, non-filler preview snippet.
    2. A list of top unique keywords for fast indexing.
    """
    if not content:
        return "", []

    # 1. Remove Markdown headers (#), bold (**), links, and code blocks
    clean_text = re.sub(r"#+\s*", "", content)
    clean_text = re.sub(r"\*\*|\*|`|~~", "", clean_text)
    clean_text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()

    # 2. Extract words and filter out stop words
    words = re.findall(r"\b[a-zA-Z0-9_-]+\b", clean_text)
    meaningful_words = []
    seen_words = set()

    for word in words:
        lower_word = word.lower()
        if lower_word not in STOP_WORDS and len(lower_word) > 2:
            if lower_word not in seen_words:
                seen_words.add(lower_word)
                meaningful_words.append(lower_word)

    # Top unique keywords
    keywords = meaningful_words[:max_keywords]

    # Clean 150-char preview snippet
    snippet = clean_text[:150].strip() + ("..." if len(clean_text) > 150 else "")

    return snippet, keywords
