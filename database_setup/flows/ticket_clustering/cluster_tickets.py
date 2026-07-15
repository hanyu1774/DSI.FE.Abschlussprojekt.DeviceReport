"""Flow: clusters the vectorized ticket texts via KMeans."""
from sklearn.cluster import KMeans

from models.vectorization_result import VectorizationResult
from models.clustering_result import ClusteringResult


class ClusterTickets:
    def run(self, vectorization: VectorizationResult, n_clusters: int) -> ClusteringResult:
        # scikit-learn's KMeans ships without type annotations for n_init; basedpyright
        # infers its type purely from the unannotated default value ("auto"), so it sees
        # only "str" even though int is a fully supported, documented value at runtime.
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)  # pyright: ignore[reportArgumentType]
        labels = kmeans.fit_predict(vectorization.matrix)

        result = ClusteringResult()
        result.labels = list(labels)
        result.cluster_centers = kmeans.cluster_centers_
        return result
