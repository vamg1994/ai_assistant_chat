import streamlit as st
from utils import get_assistant_details, create_thread, send_message
from datetime import datetime

def display_assistant_details(assistant):
    """Display information about the assistant."""
    st.subheader(assistant['name'])
    st.markdown(f"**Model:** {assistant['model']}")

    if assistant['tools']:
        st.markdown("**Available Tools:**")
        for tool in assistant['tools']:
            st.markdown(f"- {tool}")

def display_chat_message(message):
    """Display a single chat message with appropriate styling."""
    role = message["role"]
    content = message["content"]

    if role == "user":
        st.markdown(f"**You:** {content}")
    else:
        st.markdown(f"**Assistant:** {content}")

def initialize_chat_state():
    """Initialize session state for chat functionality."""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = create_thread()
    if "messages" not in st.session_state:
        st.session_state.messages = []

def main():
    st.set_page_config(
        page_title="OpenAI Assistant Chat",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 OpenAI Assistant Chat")

    # Initialize chat state
    initialize_chat_state()

    # Fetch assistant details
    with st.spinner("Loading assistant details..."):
        assistant_details = get_assistant_details()

    if not assistant_details:
        st.error("Failed to load assistant details. Please check your API key and try again.")
        return

    # Create two columns for layout
    col1, col2 = st.columns([1, 3])

    with col1:
        display_assistant_details(assistant_details)

    with col2:
        # Chat interface
        st.subheader("Chat")

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                display_chat_message(message)

        # Chat input area
        with st.container():
            # Create a form for message input
            with st.form(key="chat_form"):
                user_message = st.text_area("Type your message here", key="user_input", height=100)
                submit_button = st.form_submit_button("Send")

                if submit_button and user_message:
                    if st.session_state.thread_id:
                        with st.spinner("Processing..."):
                            messages = send_message(st.session_state.thread_id, user_message)
                            if messages:
                                st.session_state.messages = messages
                                st.rerun()
                    else:
                        st.error("Failed to create chat thread. Please refresh the page.")

if __name__ == "__main__":
    main()