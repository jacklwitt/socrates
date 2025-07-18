import streamlit as st
from character_builder import generate_characters
from memory import log_message, get_recent_messages
from logic import choose_next_speaker, generate_turn, should_teacher_intervene
from typing import Optional

st.title("🧠 Socratic Debate")

if "characters" not in st.session_state:
    question = st.text_input("Enter a debate question:")
    if question:
        st.session_state["question"] = question
        characters = generate_characters(question)
        st.session_state["characters"] = characters
        # Teacher poses the question as the first message
        teacher_msg = f"Let's begin our debate. The question is: {question}"
        log_message("Teacher", teacher_msg)
        st.session_state["turn_count"] = 0
        st.session_state["last_speaker"] = "Teacher"
        st.session_state["user_action"] = None
        st.rerun()
else:
    st.markdown("---")
    # Render conversation
    messages = get_recent_messages(50)
    # Build a mapping from character name to worldview
    if "characters" in st.session_state:
        name_to_worldview = {c["name"]: c["worldview"] for c in st.session_state["characters"]}
    else:
        name_to_worldview = {}
    for msg in messages:
        speaker = msg.get('speaker', 'Unknown')
        worldview = name_to_worldview.get(speaker)
        if worldview:
            display_name = f"{speaker} ({worldview})"
        else:
            display_name = speaker
        st.markdown(f"**{display_name}:** {msg.get('text', '')}")
    st.markdown("---")
    # Debate turn logic
    if "turn_count" not in st.session_state:
        st.session_state["turn_count"] = 0
    if "last_speaker" not in st.session_state:
        st.session_state["last_speaker"] = "Teacher"
    if "user_action" not in st.session_state:
        st.session_state["user_action"] = None
    # User options after each character's response
    user_action = st.radio(
        "What would you like to do?",
        ("Let the debate continue", "Jump in (add your message)", "Reply to a character", "Ask for a new direction"),
        index=0
    )
    if user_action == "Let the debate continue":
        if st.button("Next Turn"):
            characters = st.session_state["characters"]
            last_speaker = st.session_state["last_speaker"]
            # Pick next speaker
            try:
                next_speaker = choose_next_speaker(characters, messages, last_speaker)
            except Exception as e:
                st.error(f"Error choosing next speaker: {e}")
                next_speaker = characters[0]
            # Generate turn
            turn_text = generate_turn(next_speaker, messages)
            log_message(next_speaker["name"], turn_text)
            st.session_state["last_speaker"] = next_speaker["name"]
            st.session_state["turn_count"] += 1
            st.rerun()
    elif user_action == "Jump in (add your message)":
        user_msg = st.text_area("Your message:", key="user_msg")
        if st.button("Send Message"):
            log_message("User", user_msg)
            st.session_state["last_speaker"] = "User"
            st.session_state["turn_count"] += 1
            # Immediately continue with next character's turn
            characters = st.session_state["characters"]
            try:
                next_speaker = choose_next_speaker(characters, messages + [{"speaker": "User", "text": user_msg}], "User")
            except Exception as e:
                st.error(f"Error choosing next speaker: {e}")
                next_speaker = characters[0]
            turn_text = generate_turn(next_speaker, messages + [{"speaker": "User", "text": user_msg}])
            log_message(next_speaker["name"], turn_text)
            st.session_state["last_speaker"] = next_speaker["name"]
            st.session_state["turn_count"] += 1
            st.rerun()
    elif user_action == "Reply to a character":
        character_names = [f"{c['name']} ({c['worldview']})" for c in st.session_state["characters"]]
        # Map display name back to character name
        display_to_name = {f"{c['name']} ({c['worldview']})": c['name'] for c in st.session_state["characters"]}
        reply_to_display = st.selectbox("Which character do you want to reply to?", character_names)
        reply_to = display_to_name[reply_to_display]
        reply_msg = st.text_area("Your reply:", key="reply_msg")
        if st.button("Send Reply"):
            log_message("User", reply_msg, reply_to=reply_to)
            st.session_state["last_speaker"] = "User"
            st.session_state["turn_count"] += 1
            # Immediately continue with the replied-to character's turn
            characters = st.session_state["characters"]
            next_speaker = next(c for c in characters if c["name"] == reply_to)
            turn_text = generate_turn(next_speaker, messages + [{"speaker": "User", "text": reply_msg, "reply_to": reply_to}])
            log_message(next_speaker["name"], turn_text)
            st.session_state["last_speaker"] = next_speaker["name"]
            st.session_state["turn_count"] += 1
            st.rerun()
    elif user_action == "Ask for a new direction":
        direction_msg = st.text_area("What new direction or question do you want to pose?", key="direction_msg")
        if st.button("Send Direction"):
            if direction_msg.strip() == "":
                # LLM generates a strong new direction
                teacher_prompt = (
                    "Based on the debate so far, suggest a strong new direction or question that would push the discussion into new territory. Respond ONLY with the new direction or question, in clear, everyday language."
                )
                conversation = "\n".join([
                    f"{msg.get('speaker', 'Unknown')}: {msg.get('text', msg.get('content', ''))}" for msg in messages[-10:]
                ])
                from openai_client import call_openai
                raw_direction = call_openai([
                    {"role": "system", "content": teacher_prompt},
                    {"role": "user", "content": conversation}
                ])
                direction_msg = raw_direction.strip()
            log_message("User", direction_msg)
            st.session_state["last_speaker"] = "User"
            st.session_state["turn_count"] += 1
            # Teacher responds, pushing the new direction
            teacher_msg = generate_turn({"name": "Teacher", "background": "Debate teacher", "summary": "Moderator"}, messages + [{"speaker": "User", "text": direction_msg}], force_summary=False)
            log_message("Teacher", teacher_msg)
            st.session_state["last_speaker"] = "Teacher"
            st.session_state["turn_count"] += 1
            st.rerun()
    # Teacher intervention
    # Only intervene if last message is not from Teacher
    if should_teacher_intervene(st.session_state["turn_count"]):
        if messages and messages[-1].get("speaker") != "Teacher":
            # Only summarize relevant debate messages (from characters or user, not teacher/system)
            debate_names = [c["name"] for c in st.session_state["characters"]] + ["User"]
            relevant_messages = [m for m in messages if m.get("speaker") in debate_names]
            teacher_summary = generate_turn({"name": "Teacher", "background": "Debate teacher", "summary": "Moderator"}, relevant_messages, force_summary=True)
            # Prevent double 'Teacher:' prefix by logging as 'Teacher' and not including it in the message content
            log_message("Teacher", teacher_summary)
            st.session_state["last_speaker"] = "Teacher"
            st.session_state["turn_count"] += 1
            st.warning("The teacher has summarized the debate and may suggest a new direction!")
            st.rerun()
