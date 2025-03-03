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
    if "selected_assistant" not in st.session_state:
        st.session_state.selected_assistant = "ASSISTANT_ID"  # Default assistant

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

def handle_assistant_error(thread_id, user_message):
    """
    Handle errors when communicating with the assistant.
    Provides fallback behavior when the assistant fails to respond.
    
    Args:
        thread_id (str): The current thread ID
        user_message (str): The user's message that caused the error
        
    Returns:
        list: Updated messages list with error notification
    """
    # Log the error
    logger.error(f"Assistant failed to process message: {user_message}")
    
    # Add user message to the conversation
    st.session_state.messages.append({"role": "user", "content": user_message})
    
    # Add error message from assistant
    error_message = {
        "role": "assistant", 
        "content": "I'm sorry, I encountered an error while processing your request. This might happen when retrieving information from my knowledge base. Could you try rephrasing your question or asking something else?"
    }
    st.session_state.messages.append(error_message)
    
    return st.session_state.messages

def main():
    """Main application function."""
    # Page configuration
    st.set_page_config(
        page_title="Legal AI Assistant",
        page_icon="⚖️",
        layout="wide"
    )

    # Initialize session state
    initialize_session_state()

    # Page header
    st.header("⚖️ Legal AI Assistant")

    # Assistant selection
    assistant_options = {
        "Assistant 1": "ASSISTANT_ID",
        "Assistant 2": "ASSISTANT_ID2"
    }
    selected = st.sidebar.selectbox(
        "Select Assistant",
        options=list(assistant_options.keys())
    )
    st.session_state.selected_assistant = assistant_options[selected]

    # Load assistant details
    with st.spinner("Loading assistant..."):
        assistant_details = get_assistant_details(st.session_state.selected_assistant)
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
        # Chat input at the top
        user_message = st.chat_input("Type your message here...")
        
        # Processing spinner container - placed between input and chat
        spinner_container = st.empty()
        
        if st.session_state.messages:
            display_chat_controls()
        
        display_chat_interface()
        
        if user_message and st.session_state.thread_id:
            # Show spinner in the designated container
            with spinner_container.container():
                st.spinner("Processing...")
                
            try:
                messages = send_message(st.session_state.thread_id, user_message)
                if messages:
                    st.session_state.messages = messages
                    st.rerun()
                else:
                    # Handle case where send_message returns None or empty
                    st.session_state.messages = handle_assistant_error(
                        st.session_state.thread_id, user_message
                    )
                    st.rerun()
            except Exception as e:
                logger.exception(f"Error processing message: {str(e)}")
                st.session_state.messages = handle_assistant_error(
                    st.session_state.thread_id, user_message
                )
                st.rerun()

if __name__ == "__main__":
    main()