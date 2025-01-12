"""
Streamlit Chat Application with OpenAI Assistant Integration
This module provides a chat interface using Streamlit's native components.
"""

import streamlit as st
import json
import logging
import tiktoken
from utils import get_assistant_details, create_thread, send_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding="UTF-8"
)
logger = logging.getLogger(__name__)

def initialize_session_state() -> None:
    """
    Initialize Streamlit session state variables.
    Creates new thread and empty message list if they don't exist.
    """
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = create_thread()
    if "messages" not in st.session_state:
        st.session_state.messages = []

def get_token_count(messages: list) -> int:
    """
    Calculate total tokens used in conversation.
    Args:
        messages (list): List of conversation messages
    Returns:
        int: Total token count
    """
    enc = tiktoken.get_encoding("cl100k_base")
    text = " ".join([msg["content"] for msg in messages])
    return len(enc.encode(text))

def display_chat_controls() -> None:
    """Display chat control options: save, clear, and token count."""
    cols = st.columns([1, 1, 2])  # Simplified column layout
    
    with cols[0]:
        # Save chat button
        json_messages = json.dumps(st.session_state.messages).encode("utf-8")
        st.download_button(
            label="💾 Save Chat",
            data=json_messages,
            file_name="chat_history.json",
            mime="application/json",
        )
    
    with cols[1]:
        # Clear chat button
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.thread_id = create_thread()
            st.rerun()
    
    with cols[2]:
        # Token counter
        token_count = get_token_count(st.session_state.messages)
        st.link_button(
            f"🔤 {token_count} tokens", 
            "https://platform.openai.com/tokenizer"
        )

def display_chat_interface() -> None:
    """Display the main chat interface with message history."""
    # Chat container with scrolling
    chat_container = st.container()
    with chat_container:
        st.markdown("""
            <style>
                .stChatContainer {
                    height: 450px;
                    overflow-y: auto;
                    padding: 1rem;
                    background-color: #f8f9fa;
                    border-radius: 0.5rem;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Display message history
        for message in st.session_state.messages:
            with st.chat_message(
                message["role"],
                avatar="🤖" if message["role"] == "assistant" else "👤"
            ):
                st.write(message["content"])

def main():
    """Main application function."""
    # Page configuration
    st.set_page_config(
        page_title="AI Assistant",
        page_icon="🤖",
        layout="wide"
    )

    # Initialize session state
    initialize_session_state()

    # Page header
    st.header("🤖 AI Assistant")

    # Load assistant details
    with st.spinner("Loading assistant..."):
        assistant_details = get_assistant_details()
        if not assistant_details:
            st.error("Failed to load assistant. Please check your configuration.")
            return

    # Main layout
    info_col, chat_col = st.columns([1, 3])

    # Assistant information sidebar
    with info_col:
        st.subheader(assistant_details['name'])
        st.markdown(f"**Model:** {assistant_details['model']}")
        if assistant_details['tools']:
            st.markdown("**Available Tools:**")
            for tool in assistant_details['tools']:
                st.markdown(f"- {tool}")

    # Chat interface
    with chat_col:
        if st.session_state.messages:
            display_chat_controls()
        
        display_chat_interface()

        # Chat input
        user_message = st.chat_input("Type your message here...")
        
        if user_message and st.session_state.thread_id:
            with st.spinner("Processing..."):
                messages = send_message(st.session_state.thread_id, user_message)
                if messages:
                    st.session_state.messages = messages
                    st.rerun()

if __name__ == "__main__":
    main()