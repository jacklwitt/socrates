from typing import Optional
from openai_client import call_openai

def choose_next_speaker(characters: list[dict], memory: list[dict], last_speaker: Optional[str]) -> dict:
    """
    Uses the LLM to select the next character to speak, based on the conversation so far.
    The LLM is instructed to pick the character whose perspective is most relevant for the next turn,
    ensuring no one or two characters dominate, and the same character does not speak twice in a row.
    """
    if not characters:
        raise ValueError("No characters available to choose from.")
    if len(characters) == 1:
        return characters[0]
    # Prepare prompt for LLM
    character_summaries = "\n".join([
        f"- {c['name']} ({c['worldview']}): {c['summary']}" for c in characters
    ])
    conversation = "\n".join([
        f"{msg.get('speaker', 'Unknown')}: {msg.get('text', msg.get('content', ''))}" for msg in memory[-10:]
    ])
    prompt = f"""
You are moderating a lively debate. Here are the characters:
{character_summaries}

Here is the recent conversation:
{conversation}

The last speaker was: {last_speaker}

Pick the character (by name) whose perspective is most relevant to respond next. Do not pick the same character twice in a row, and avoid letting any one or two characters dominate the conversation. Choose the character who can best move the discussion forward or provide a new angle. Respond ONLY with the character's name.
"""
    response = call_openai([
        {"role": "system", "content": prompt}
    ])
    # Extract the name from the response
    name = response.strip().split("\n")[0]
    for c in characters:
        if c["name"].lower() == name.lower():
            return c
    # Fallback: pick the first eligible character
    for c in characters:
        if c["name"] != last_speaker:
            return c
    return characters[0]


def generate_turn(speaker: dict, messages: list[dict], force_summary: bool = False) -> str:
    """
    Builds a GPT prompt using the speaker's background and recent messages. Calls call_openai() and returns the response string.
    The response should be brief (no more than 2 paragraphs, but can be as short as 1-2 sentences if that suffices), and should mimic a real-life debate: build on previous points, either answering directly, returning to the main point, adding complexity, or introducing a new line of argument. Respond naturally, as if in a live discussion. Avoid unnecessary fluff or repetition; be concise and substantive.
    If force_summary is True, the speaker should summarize the debate so far in only 1-3 sentences, focusing on what has been mentioned (not addressing specific people's points or proposing new directions unless absolutely necessary). The summary should be concise, non-repetitive, and avoid apologies or meta-comments.
    """
    stance = speaker.get('stance', speaker.get('summary', 'No stance provided.'))
    if force_summary:
        system_prompt = (
            f"You are {speaker['name']}, {speaker['background']}. Your stance: {stance}. "
            "Your task is to briefly summarize what has been discussed in the debate so far, in only 1-3 sentences. Do not address specific people's points, do not propose new directions unless absolutely necessary, and do not apologize or make meta-comments. Be concise and avoid repetition."
        )
    else:
        system_prompt = (
            f"You are {speaker['name']}, {speaker['background']}. Your stance: {stance}. "
            "Respond to the discussion in character. Take a strong, clear stance on the issue, and do not hedge or remain neutral. Offer a direct answer to the question or topic at hand. Almost always back up your points with specific examples, concrete data, statistics, or references to real-world events, studies, or historical cases. Provide unique insights or reasoning that go beyond generalities. Your response should be brief (no more than 2 paragraphs, but as short as 1-2 sentences if that suffices). Mimic a real-life debate: build on the previous points in the conversation—either answer the last message directly, return to the main point, add a new level of complexity, or introduce a new line of argument. Respond naturally, as if in a live discussion. Avoid unnecessary fluff or repetition; be concise and substantive."
        )
    openai_messages = [
        {"role": "system", "content": system_prompt}
    ]
    # Only include the last 3 messages to reduce token usage
    for msg in messages[-3:]:
        role = "assistant" if msg.get('speaker') == speaker['name'] else "user"
        openai_messages.append({
            "role": role,
            "content": f"{msg.get('speaker', 'Unknown')}: {msg.get('text', msg.get('content', ''))}"
        })
    response = call_openai(openai_messages)
    return response


def should_teacher_intervene(turn_count: int) -> bool:
    """
    Returns True only every 5 turns (i.e., on turns 5, 10, 15, ...).
    """
    return turn_count != 0 and turn_count % 5 == 0
