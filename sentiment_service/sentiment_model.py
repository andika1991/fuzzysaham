import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


corpus = pd.read_csv(
    "corpus/corpus_sentimen.csv",
    sep=",",
    quotechar='"',
    engine="python",
    on_bad_lines="skip"
)

corpus = corpus.dropna(subset=["text", "label"])
corpus["text"] = corpus["text"].astype(str)
corpus["label"] = corpus["label"].astype(int)

vectorizer = TfidfVectorizer()
tfidf = vectorizer.fit_transform(corpus["text"])
labels = corpus["label"].tolist()


def classify_sentiment(text):
    if not text:
        return "netral"

    v = vectorizer.transform([text])
    sims = cosine_similarity(v, tfidf).flatten()

    score = {}

    for label in [0, 1, 2]:
        indexes = [i for i, l in enumerate(labels) if l == label]

        if indexes:
            score[label] = sims[indexes].mean()
        else:
            score[label] = 0

    label_map = {
        0: "positif",
        1: "netral",
        2: "negatif"
    }

    return label_map[max(score, key=score.get)]