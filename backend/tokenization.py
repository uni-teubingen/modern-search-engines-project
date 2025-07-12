# Tokenization
# Tokenize a given raw text for later use, either for indexing or ranking
import spacy


# Tokenize a given text into singular Tokens and the total number of their occurences
# @param text : String
# Return set(String -> Int)
def tokenize(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    tokens: dict[str, int] = {}
    for token in doc:
        if token.is_stop or token.is_punct or token.is_space or token.like_num or token.is_quote:
            continue
        lemmatized_token = token.lemma.casefold()

        if(len(lemmatized_token) == 1): #or not lemmatized_token.isalpha()
            continue

        tokens[lemmatized_token] = tokens.get(lemmatized_token, 0) + 1
    return tokens

