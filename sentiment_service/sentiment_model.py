import numpy as np
import pandas as pd
from imblearn.over_sampling import RandomOverSampler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==========================================
# LOAD CORPUS
# ==========================================
corpus = pd.read_csv("corpus/corpus_sentimen_clean.csv")

corpus = corpus.dropna(subset=["text", "label"])
corpus["text"] = corpus["text"].astype(str)
corpus["label"] = corpus["label"].astype(int)

# ==========================================
# OVERSAMPLING
# ==========================================
ros = RandomOverSampler(random_state=42)

X_res, y_res = ros.fit_resample(
    corpus[["text"]],
    corpus["label"]
)

train_bal = pd.DataFrame({
    "text": X_res["text"],
    "label": y_res
})

# ==========================================
# TF-IDF
# ==========================================
vectorizer = TfidfVectorizer(
    max_features=7000,
    ngram_range=(1,2),
    sublinear_tf=True
)

X_train_vec = vectorizer.fit_transform(train_bal["text"])

y_train_bal = train_bal["label"].reset_index(drop=True)

label_map = {
    0: "positif",
    1: "netral",
    2: "negatif"
}

TOP_K = 20

# ==========================================
# PREDIKSI SENTIMEN
# ==========================================
def classify_sentiment(text, top_k=TOP_K):

    if pd.isna(text) or str(text).strip() == "":
        return "netral"

    vec = vectorizer.transform([str(text)])

    sim = cosine_similarity(vec, X_train_vec)[0]

    score = {}

    for label in sorted(y_train_bal.unique()):

        sim_label = sim[y_train_bal == label]

        if len(sim_label) > top_k:
            top = np.partition(sim_label, -top_k)[-top_k:]
        else:
            top = sim_label

        score[label] = np.mean(top)

    return label_map[max(score, key=score.get)]