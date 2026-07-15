"""Model: raw output of the clustering algorithm."""
import numpy
from numpy.typing import NDArray


class ClusteringResult:
    def __init__(self):
        self.labels: list[int] = []                                    # cluster assignment per document
        self.cluster_centers: NDArray[numpy.float64] = numpy.empty((0, 0))   # cluster centers (used to derive top terms)
