import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

def test_api_key_and_model():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    assert api_key is not None and len(api_key) > 0, "GOOGLE_API_KEY not found in environment"
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=api_key)
    assert llm.model == "gemini-3.6-flash"
