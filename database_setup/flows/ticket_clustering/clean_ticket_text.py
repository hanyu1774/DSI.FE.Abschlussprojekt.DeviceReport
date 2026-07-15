"""Flow: cleans ticket free text before vectorization."""
import re


class CleanTicketText:
    """
    Removes machine names and numbers from the text. Otherwise they dominate
    the TF-IDF features and clusters group by machine instead of by root
    cause. Hyphens/digits are replaced with a space (not deleted!), so that
    compound words like "Steuerungssoftware-Kalibrierung" don't collapse
    into a single, new token.
    """

    def run(self, descriptions: list[str]) -> list[str]:
        MACHINE_WORDS = ["foerderband", "paketroboter", "trockner", "kuehltunnel", "etikettierer"]
        cleaned = []
        for text in descriptions:
            lowered = text.lower()
            for word in MACHINE_WORDS:
                lowered = lowered.replace(word, "")
            lowered = re.sub(r"[\d\-]+", " ", lowered)
            cleaned.append(lowered)
        return cleaned
