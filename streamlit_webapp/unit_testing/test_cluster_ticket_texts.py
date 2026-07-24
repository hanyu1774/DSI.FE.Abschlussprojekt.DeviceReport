import warnings

import pandas as pd
import pytest
from sklearn.exceptions import ConvergenceWarning

from flows.cluster_ticket_texts import ClusterTicketTexts

# TfidfVectorizer uses min_df=2 and max_df=0.12 - a term needs to appear in
# at least 2 documents but no more than 12% of them, which needs a corpus
# large enough for that window to exist at all (roughly 25+ documents).
# Structural properties are asserted, not exact cluster membership - the
# point is verifying the Flow's own logic (size accounting, id uniqueness,
# n_clusters capping), not whether TF-IDF finds "good" clusters.
_DESCRIPTIONS = [
    "Sensor meldet Fehlfunktion am Trockner", "Sensor zeigt falsche Werte an",
    "Sensor Kalibrierung erforderlich", "Motor laeuft unrund seit heute",
    "Motor macht ungewoehnliche Geraeusche", "Motor Temperatur zu hoch",
    "Foerderband blockiert durch Fremdkoerper", "Foerderband stoppt zufaellig",
    "Foerderband Antrieb defekt", "Kuehlung faellt regelmaessig aus",
    "Kuehlung erreicht Zieltemperatur nicht", "Software zeigt Fehlercode E404",
    "Software Absturz beim Start", "Software Update fehlgeschlagen",
    "Ersatzteil fuer Dichtung benoetigt", "Dichtung undicht am Ventil",
    "Ventil klemmt seit Wartung", "Ventil laesst sich nicht oeffnen",
    "Bediener meldet Vibration am Gehaeuse", "Vibration nimmt staendig zu",
    "Wartungsintervall ueberschritten fuer Anlage", "Anlage benoetigt Generalueberholung",
    "Stromversorgung unterbrochen am Vormittag", "Stromversorgung schwankt staendig",
    "Display zeigt keine Werte an", "Display bleibt dunkel nach Neustart",
    "Filter verstopft nach kurzer Zeit", "Filter muss haeufiger gewechselt werden",
    "Kupplung schleift beim Anfahren", "Kupplung erzeugt Reibungsgeraeusche",
]


def _descriptions_df(n: int = len(_DESCRIPTIONS)) -> pd.DataFrame:
    return pd.DataFrame({
        "id": range(1, n + 1),
        "ticket_type": ["Incident"] * n,
        "description": _DESCRIPTIONS[:n],
        "error_category": (["Elektrik", "Mechanik", "Software"] * n)[:n],
    })


def test_empty_input_returns_empty_list():
    empty = pd.DataFrame(columns=["id", "ticket_type", "description", "error_category"])
    assert ClusterTicketTexts().run(empty, n_clusters=3) == []


def test_every_ticket_is_accounted_for_across_clusters():
    result = ClusterTicketTexts().run(_descriptions_df(), n_clusters=4)
    assert sum(cluster["size"] for cluster in result) == len(_DESCRIPTIONS)


def test_cluster_ids_are_unique():
    result = ClusterTicketTexts().run(_descriptions_df(), n_clusters=4)
    ids = [cluster["cluster_id"] for cluster in result]
    assert len(ids) == len(set(ids))


def test_sorted_by_size_descending():
    result = ClusterTicketTexts().run(_descriptions_df(), n_clusters=4)
    sizes = [cluster["size"] for cluster in result]
    assert sizes == sorted(sizes, reverse=True)


def test_n_clusters_capped_when_requesting_more_than_available_documents():
    subset = _descriptions_df(n=20)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ConvergenceWarning)
        result = ClusterTicketTexts().run(subset, n_clusters=50)
    assert sum(cluster["size"] for cluster in result) == 20
    assert len(result) <= 20


def test_too_few_documents_currently_raises():
    """Documents a real, pre-existing limitation (not introduced by the
    restructure): TfidfVectorizer(min_df=2, max_df=0.12) requires roughly
    17+ documents just for that window to be mathematically satisfiable at
    all. Below that, this Flow raises instead of degrading gracefully - e.g.
    a heavily filtered ticket list could 500 the /tickets/clusters endpoint.
    This test pins down today's actual behavior; if you fix the Flow to
    handle small inputs gracefully, this test should start failing and
    needs updating to match, not deleting."""
    with pytest.raises(ValueError):
        ClusterTicketTexts().run(_descriptions_df(n=5), n_clusters=2)
