"""Flow: derives a readable label (top terms) from each cluster's center."""
import numpy

from models.vectorization_result import VectorizationResult
from models.clustering_result import ClusteringResult


class LabelClusters:

    def run(self, clustering: ClusteringResult, vectorization: VectorizationResult,
            n_clusters: int) -> dict[int, str]:

        TOP_TERMS_PER_CLUSTER = 5
        terms = numpy.array(vectorization.feature_names)
        labels_by_cluster = {}

        for cluster_id in range(n_clusters):
            top_indices = clustering.cluster_centers[cluster_id].argsort()[::-1][:TOP_TERMS_PER_CLUSTER]
            top_terms = [t for t in terms[top_indices] if t]
            labels_by_cluster[cluster_id] = " / ".join(top_terms)

        return labels_by_cluster
