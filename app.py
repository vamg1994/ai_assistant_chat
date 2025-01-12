import streamlit as st
import json
import logging
import tiktoken
from datetime import datetime
from utils import get_assistant_details, create_thread, send_message

# Setup logging
logger = logging.getLogger()
logging.basicConfig(encoding="UTF-8", level=logging.INFO)

def log_feedback(icon):
    """Log user feedback for the last conversation."""
    st.toast("Thanks for your feedback!", icon="👌")
    last_messages = json.dumps(st.session_state.messages[-2:])
    activity = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: "
    activity += f"{'positive' if icon == '👍' else 'negative'}: {last_messages}"
    logger.info(activity)

def initialize_chat_state():
    """Initialize session state for chat functionality."""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = create_thread()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "rerun" not in st.session_state:
        st.session_state.rerun = False

def display_chat_options():
    """Display chat control options and information."""
    cols = st.columns([7, 19.4, 19.3, 9, 8.6, 8.6, 28.1])
    
    with cols[1]:
        json_messages = json.dumps(st.session_state.messages).encode("utf-8")
        st.download_button(
            label="📥 Save chat!",
            data=json_messages,
            file_name="chat_conversation.json",
            mime="application/json",
        )
    
    with cols[2]:
        if st.button("Clear Chat 🧹"):
            st.session_state.messages = []
            st.session_state.thread_id = create_thread()
            st.rerun()
            
    with cols[3]:
        if st.button("🔁"):
            st.session_state.rerun = True
            st.rerun()
            
    with cols[4]:
        if st.button("👍"):
            log_feedback("👍")
            
    with cols[5]:
        if st.button("👎"):
            log_feedback("👎")
            
    with cols[6]:
        enc = tiktoken.get_encoding("cl100k_base")
        tokenized_text = enc.encode(" ".join([msg["content"] for msg in st.session_state.messages]))
        label = f"💬 {len(tokenized_text)} tokens"
        st.link_button(label, "https://platform.openai.com/tokenizer")

def main():
    st.set_page_config(
        page_title="AI Assistant Chat",
        page_icon="🤖",
        layout="wide"
    )

    st.markdown("""
        <nav class="navbar" style="
            background-color: #f0f2f6;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 0.5rem;
        ">
            <h1 style="margin: 0;">🤖 AI Assistant Chat</h1>
        </nav>
    """, unsafe_allow_html=True)

    initialize_chat_state()

    with st.spinner("Loading assistant details..."):
        assistant_details = get_assistant_details()

    if not assistant_details:
        st.error("Failed to load assistant details. Please check your API key and try again.")
        return

    col1, col2 = st.columns([1, 3])

    with col1:
        st.subheader(assistant_details['name'])
        st.markdown(f"**Model:** {assistant_details['model']}")
        if assistant_details['tools']:
            st.markdown("**Available Tools:**")
            for tool in assistant_details['tools']:
                st.markdown(f"- {tool}")

    with col2:
        st.subheader("Chat")
        
        # Display chat options if there are messages
        if st.session_state.messages:
            display_chat_options()

        # Chat history container
        chat_container = st.container()
        with chat_container:
            st.markdown("""
                <style>
                    .stChatContainer {
                        height: 400px;
                        overflow-y: scroll;
                        padding: 1rem;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            for message in st.session_state.messages:
                with st.chat_message(
                    message["role"],
                    avatar="🤖" if message["role"] == "assistant" else "👤"
                ):
                    st.write(message["content"])

        # Chat input
        user_message = st.chat_input("How can I help you?")
        
        if user_message or st.session_state.rerun:
            if st.session_state.thread_id:
                with st.spinner("Processing..."):
                    messages = send_message(
                        st.session_state.thread_id,
                        user_message if user_message else st.session_state.messages[-2]["content"]
                    )
                    if messages:
                        st.session_state.messages = messages
                        st.session_state.rerun = False
                        st.rerun()
            else:
                st.error("Failed to create chat thread. Please refresh the page.")

if __name__ == "__main__":
    main()