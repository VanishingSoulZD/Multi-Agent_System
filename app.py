import streamlit as st

from utils.openai_api import chat_with_gpt

st.set_page_config(page_title="LLM Chatbot Demo", page_icon="🤖")

st.title("🎉 我的第一个 LLM 应用 — Chatbot Demo")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "请总是以滑稽的方式回答，回答要简洁",
        }
    ]


def user_input():
    input_text = st.text_input("你想问点什么？", "")
    return input_text


user_question = user_input()

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    response = chat_with_gpt(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": response})

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**用户:** {msg['content']}")
    else:
        st.markdown(f"**助手:** {msg['content']}")
