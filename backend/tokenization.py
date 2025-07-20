import re
from string import punctuation

stopwords = set([
    "the", "and", "is", "of", "in", "to", "with", "that", "as", "for", "on",
    "was", "are", "by", "this", "from", "be", "or", "an", "it"
])

def tokenize(text):
    tokens = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    return [t for t in tokens if t not in stopwords]