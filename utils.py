import os
from openai import OpenAI
from typing import Dict, List
import streamlit as st
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def init_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found. Please check your .env file.")
        st.stop()
    return OpenAI(api_key=api_key)

def get_assistant_details(assistant_id: str = "ASSISTANT_ID") -> dict:
    """
    Get assistant details from OpenAI.
    Args:
        assistant_id (str): The ID of the assistant to use
    Returns:
        dict: Assistant details
    """
    try:
        client = init_openai_client()
        assistant_id_value = os.getenv(assistant_id)
        
        if not assistant_id_value:
            st.error(f"Assistant ID not found for {assistant_id}. Please check your .env file.")
            st.write(f"Available environment variables: {os.environ.keys()}")  # Debug line
            return None
            
        assistant = client.beta.assistants.retrieve(assistant_id_value)
        return {
            'name': assistant.name,
            'model': assistant.model,
            'tools': [tool.type for tool in assistant.tools]
        }
    except Exception as e:
        st.error(f"Error getting assistant details: {e}")
        return None

def create_thread() -> str:
    """Create a new thread for the conversation."""
    try:
        client = init_openai_client()
        thread = client.beta.threads.create()
        return thread.id
    except Exception as e:
        st.error(f"Error creating thread: {str(e)}")
        return ""

def send_message(thread_id: str, user_message: str) -> List[Dict]:
    """Send a message to the assistant and get the response."""
    try:
        client = init_openai_client()

        # Add the user message to the thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Run the assistant using the selected assistant ID from session state
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=os.getenv(st.session_state.selected_assistant)
        )

        # Wait for the run to complete with timeout
        start_time = time.time()
        timeout = 30  # 30 seconds timeout

        while True:
            if time.time() - start_time > timeout:
                st.error("Request timed out. Please try again.")
                return []

            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

            if run.status == "completed":
                break
            elif run.status in ["failed", "cancelled", "expired"]:
                st.error(f"Run failed with status: {run.status}")
                return []
            elif run.status in ["queued", "in_progress"]:
                time.sleep(0.5)
            else:
                st.error(f"Unexpected run status: {run.status}")
                return []

        # Get all messages from the thread
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Convert messages to a list of dictionaries
        message_list = []
        for msg in messages:
            message_list.append({
                "role": msg.role,
                "content": msg.content[0].text.value if msg.content else ""
            })

        return message_list

    except Exception as e:
        st.error(f"Error in chat interaction: {str(e)}")
        return []