"""Model: result of the text vectorization step (TF-IDF matrix + term list)."""
from scipy.sparse import csr_matrix


class VectorizationResult:
    def __init__(self):
        self.matrix: csr_matrix = csr_matrix((0, 0))   # sparse TF-IDF matrix
        self.feature_names: list[str] = []
