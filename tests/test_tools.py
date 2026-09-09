from agent.tools import web_search, fetch_web_page, evaluate_python_code

def test_evaluate_python_code_valid():
    valid_code = "x = 10\ny = 20\nresult = x + y\nprint(result)"
    res = evaluate_python_code.invoke({"code": valid_code})
    assert "Syntax OK" in res

def test_evaluate_python_code_invalid():
    invalid_code = "def foo(:"
    res = evaluate_python_code.invoke({"code": invalid_code})
    assert "Syntax Error" in res or "Error" in res

def test_web_search_tool():
    res = web_search.invoke({"query": "LangGraph Python"})
    assert isinstance(res, str)
    assert len(res) > 0
