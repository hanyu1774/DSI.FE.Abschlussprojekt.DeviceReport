"""Flow: turns cleaned ticket texts into a TF-IDF matrix."""
from typing import cast

from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from models.vectorization_result import VectorizationResult


class VectorizeTicketText:
    # A small, fixed German stopword list - no runtime download (e.g. an
    # nltk corpus) needed, so this also works reliably offline.

    def run(self, cleaned_texts: list[str]) -> VectorizationResult:

        GERMAN_STOPWORDS = [
            "der", "die", "das", "und", "ist", "an", "am", "im", "in", "mit", "bei", "fuer",
            "von", "zu", "auf", "wurde", "wird", "nach", "vor", "ueber", "unter", "ein", "eine",
            "einer", "eines", "den", "dem", "des", "sich", "nicht", "mehr", "noch", "auch",
            "als", "aus", "so", "es", "sind", "war", "werden", "kann", "muss", "bitte",
            "deutlich", "stark",
        ]
        vectorizer = TfidfVectorizer(
            stop_words=GERMAN_STOPWORDS, min_df=2, ngram_range=(1, 2), sublinear_tf=True,
        )
        matrix = cast(csr_matrix, vectorizer.fit_transform(cleaned_texts))

        result = VectorizationResult()
        result.matrix = matrix
        result.feature_names = list(vectorizer.get_feature_names_out())
        return result
