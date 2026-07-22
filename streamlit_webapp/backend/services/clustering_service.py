"""
Ticket-Clustering per TF-IDF + KMeans auf den Freitext-Beschreibungen.

Dient als EDA-Explorationshilfe, um wiederkehrende Themen in Incidents/
Service-Requests zu erkennen, die sich nicht schon anhand von
Fehlercode/Kategorie erschliessen (z. B. bei Service Requests, die
keinen Fehlercode haben).
"""

from __future__ import annotations

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy import select
from sqlalchemy.engine import Engine

from models import ErrorCode, Ticket, TicketType
from services.db_utils import load_dataframe

# Equivalent of the old TICKETS_TEXT_QUERY string constant.
TICKETS_TEXT_SELECT = (
    select(
        Ticket.ticket_id.label("id"),
        TicketType.ticket_type_name.label("ticket_type"),
        Ticket.ticket_description.label("description"),
        ErrorCode.category.label("error_category"),
    )
    .join(TicketType, TicketType.ticket_type_id == Ticket.ticket_type_id)
    .outerjoin(ErrorCode, ErrorCode.error_code == Ticket.error_code)
)

# Deutsche Stoppwoerter + Formulierungen, die in fast jedem Ticket
# vorkommen ("Bediener meldet:", "Seit Schichtbeginn:", ...) und daher
# keine Unterscheidungskraft fuers Clustering haben.
GERMAN_STOPWORDS = frozenset(
    """
    aber alle als also am an auch auf aus bei bin bis bist da damit dann
    der den des dem die das dass dafuer dazu dein deine denn derselbe
    dessen dich dir doch dort du durch ein eine einem einen einer eines
    er es etwa etwas euer eure fuer gegen gemeldet gemaess habe haben hat
    hatte hatten hier hin hinter ich ihr ihre ihrer im in indem ins ist
    ja je jede jedem jeden jeder jedes jener jetzt kann kannst koennen
    koennt laut machen mehr mein meine mit muss musste nach nachdem nein
    nicht noch nun nur oder seid sein seine seit sich sie sind so solche
    soll sollte sondern sonst ueber um und uns unser unter viel vom von
    vor waehrend wann war waren warum was weiter weitere welche wenn wer
    werde werden wie wieder will wir wird wirst wo wollen wollte wuerde
    wuerden zu zum zur zwar zwischen bediener meldet rundgang festgestellt
    schichtbeginn meldung produktion bitte pruefen beheben zeitnah
    wiederholt aufgetreten ca prozent qualitaet aktuell sichergestellt
    vorsorglich wurde gestoppt anlage ersatzteilbedarf klaeren
    eingeschraenkt laeuft weiter angefordert
    """.split()
)


def cluster_tickets(engine: Engine, n_clusters: int) -> list[dict]:
    df = load_dataframe(TICKETS_TEXT_SELECT, engine)
    n_tickets = len(df)
    if n_tickets == 0:
        return []

    n_clusters = max(1, min(n_clusters, n_tickets))

    vectorizer = TfidfVectorizer(
        max_features=300,
        stop_words=list(GERMAN_STOPWORDS),
        ngram_range=(1, 2),
        min_df=2,
        # max_df filtert Begriffe, die in sehr vielen Tickets vorkommen (z. B.
        # wiederkehrende Textbausteine wie "Qualitaet aktuell nicht
        # sichergestellt") automatisch heraus - robuster als jede Floskel
        # einzeln in GERMAN_STOPWORDS zu erraten.
        max_df=0.12,
    )
    matrix = vectorizer.fit_transform(df["description"])
    terms = vectorizer.get_feature_names_out()

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(matrix)
    df = df.assign(cluster=labels)

    centroids = model.cluster_centers_
    clusters: list[dict] = []
    for cluster_id in range(n_clusters):
        subset = df[df["cluster"] == cluster_id]
        if subset.empty:
            continue

        top_term_idx = centroids[cluster_id].argsort()[::-1][:6]
        top_keywords = [terms[i] for i in top_term_idx if centroids[cluster_id][i] > 0]

        dominant_category = None
        categories = subset["error_category"].dropna()
        if not categories.empty:
            dominant_category = str(categories.value_counts().idxmax())

        examples = subset["description"].drop_duplicates().head(3).tolist()

        clusters.append(
            {
                "cluster_id": int(cluster_id),
                "size": int(len(subset)),
                "top_keywords": top_keywords,
                "dominant_category": dominant_category,
                "example_descriptions": examples,
            }
        )

    clusters.sort(key=lambda item: item["size"], reverse=True)
    return clusters
