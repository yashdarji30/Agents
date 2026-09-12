import ast
import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

@tool
def web_search(query: str) -> str:
    """Searches the web using DuckDuckGo to find documentation, guides, and technical information.
    
    Args:
        query: Search topic or keywords.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return f"No web search results found for query: '{query}'"
            formatted = []
            for idx, r in enumerate(results, 1):
                title = r.get("title", "No Title")
                body = r.get("body", "No Description")
                href = r.get("href", "#")
                formatted.append(f"[{idx}] {title}\nURL: {href}\nSnippet: {body}\n")
            return "\n---\n".join(formatted)
    except Exception as e:
        return f"Error executing web search: {str(e)}"

@tool
def fetch_web_page(url: str) -> str:
    """Fetches and extracts clean text content from a web page URL.
    
    Args:
        url: The web URL to inspect.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove script, style, and navigation tags
        for element in soup(["script", "style", "nav", "header", "footer"]):
            element.decompose()
            
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)
        return cleaned_text[:3000] if len(cleaned_text) > 3000 else cleaned_text
    except Exception as e:
        return f"Error fetching web page at '{url}': {str(e)}"

@tool
def evaluate_python_code(code: str) -> str:
    """Parses and checks the syntax validity of a Python code snippet.
    
    Args:
        code: Python source code string.
    """
    try:
        ast.parse(code)
        return "Syntax OK: Code compiled and validated successfully."
    except SyntaxError as se:
        return f"Syntax Error on line {se.lineno}: {se.msg}"
    except Exception as e:
        return f"Validation Error: {str(e)}"
