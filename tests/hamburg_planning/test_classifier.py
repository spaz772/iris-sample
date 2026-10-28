from app.integrations.hamburg_planning.classifier import classify_signal


def test_port_logistics_classification_is_explainable() -> None:
    result = classify_signal({"description": "Aenderung Hafen Logistik Terminal"})

    assert "port_logistics" in result.signal_types
    assert "hafen" in result.matched_terms
    assert result.status == "classified"


def test_unmatched_record_remains_unclassified() -> None:
    result = classify_signal({"plan": "Hamburg Testplan"})

    assert result.signal_types == ()
    assert result.matched_terms == ()
    assert result.status == "unclassified"
