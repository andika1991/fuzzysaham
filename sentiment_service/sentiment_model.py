import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

corpus = pd.read_csv("corpus/corpus_sentimen.csv")

vectorizer = TfidfVectorizer()
tfidf = vectorizer.fit_transform(corpus["text"])
labels = corpus["label"].tolist()

def classify_sentiment(text):
    v = vectorizer.transform([text])
    sims = cosine_similarity(v, tfidf).flatten()

    score = {
        0: sims[[i for i,l in enumerate(labels) if l == 0]].mean(),
        1: sims[[i for i,l in enumerate(labels) if l == 1]].mean(),
        2: sims[[i for i,l in enumerate(labels) if l == 2]].mean()
    }

    label_map = {0:"negatif", 1:"netral", 2:"positif"}
    return label_map[max(score, key=score.get)]
