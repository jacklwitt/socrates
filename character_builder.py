import json

CHARACTER_GEN_PROMPT = """
You are a world-class debate organizer. A user is exploring the question below.

Your task is to design 3-4 fictional characters, each with a unique and clearly different perspective relevant to the topic. At least some characters should have opposing or conflicting views, so that a lively debate with disagreement is possible. Avoid creating characters who would simply agree with each other.

Each character should have the following fields:
- name: (string) The character's name
- background: (string) A short background
- worldview: (string) A specific worldview or discipline (e.g. economist, rural mayor, social justice advocate)
- summary: (string) A one-sentence summary of their stance on the question

Be diverse in backgrounds and disciplines. Make sure the characters' stances are distinct and, where possible, in disagreement. Use clear, everyday language—intellectual, but not overly complex or academic. The debate should be accessible and engaging for a general audience.

Here's the question:

"{question}"

Return ONLY a valid JSON array of character objects, like this:
[
  {{
    "name": "...",
    "background": "...",
    "worldview": "...",
    "summary": "..."
  }},
  ...
]
"""

from openai_client import call_openai

def parse_characters_from_response(raw_response: str) -> list[dict]:
    """
    Attempts to parse the LLM response into a list of character dicts.
    Tries to extract the first JSON-like list from the response.
    """
    try:
        # Try direct JSON parse
        return json.loads(raw_response)
    except Exception:
        # Try to extract the first JSON-like list from the response
        import re
        match = re.search(r'\[.*\]', raw_response, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except Exception:
                pass
        # Fallback: return empty list
        return []

def generate_characters(question):
    prompt = CHARACTER_GEN_PROMPT.format(question=question)
    raw_response = call_openai([{"role": "system", "content": prompt}])
    return parse_characters_from_response(raw_response)
