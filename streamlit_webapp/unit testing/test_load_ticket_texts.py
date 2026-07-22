from flows.load_ticket_texts import LoadTicketTexts


def test_loads_ticket_descriptions_with_category(seeded_engine):
    df = LoadTicketTexts().run(seeded_engine)
    assert len(df) == 3
    assert "description" in df.columns
    assert "error_category" in df.columns
