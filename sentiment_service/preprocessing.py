import re
import string
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

stopwords = set(StopWordRemoverFactory().get_stop_words())
stemmer = StemmerFactory().create_stemmer()

def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\d+', '', text)
    text = text.translate(str.maketrans('', '', string.punctuation))
    words = [w for w in text.split() if w not in stopwords]
    return " ".join(stemmer.stem(w) for w in words)
