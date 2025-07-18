from dotenv import load_dotenv
import openai
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")

def call_openai(messages: list[dict]) -> str:
    """
    Sends the messages to OpenAI's Chat Completions API using GPT-3.5-turbo and returns the response content.
    """
    response = openai.chat.completions.create(
        model=MODEL,
        messages=messages  # type: ignore
    )
    return response.choices[0].message.content or ""
