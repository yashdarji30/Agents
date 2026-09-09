from agent.tutorial_content import GET_TUTORIAL_CATALOG

def test_tutorial_catalog_integrity():
    catalog = GET_TUTORIAL_CATALOG()
    assert "State & Schema" in catalog
    assert "Nodes & Edges" in catalog
    assert "Tool Integration" in catalog
    assert "Checkpointer Memory" in catalog
    for title, module in catalog.items():
        assert "description" in module
        assert "code" in module
