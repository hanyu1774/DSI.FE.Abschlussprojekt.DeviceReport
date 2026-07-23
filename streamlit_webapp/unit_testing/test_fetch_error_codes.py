from flows.fetch_error_codes import FetchErrorCodes


def test_returns_all_error_codes(seeded_session):
    rows = FetchErrorCodes().run(seeded_session)
    codes = {row["error_code"] for row in rows}
    assert codes == {"E101", "E202"}


def test_join_resolves_machine_type_name(seeded_session):
    rows = FetchErrorCodes().run(seeded_session)
    by_code = {row["error_code"]: row for row in rows}
    assert by_code["E101"]["machine_type"] == "Trockner"
    assert by_code["E202"]["machine_type"] == "Kuehltunnel"
    assert by_code["E101"]["severity"] == "high"
