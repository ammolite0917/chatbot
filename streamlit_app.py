import streamlit as st
from google import genai

# Show title and description.
st.title("💬 Gemini Chatbot")
st.write(
    "This is a simple chatbot that uses Google's Gemini model to generate responses."
)

# Load Gemini API key from Streamlit Secrets
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("Gemini API key is not configured in Streamlit Secrets. Please set it up in the app settings.")
    st.stop()

# Create a Gemini client.
client = genai.Client(api_key=gemini_api_key)

# Create a session state variable to store the chat messages.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display the existing chat messages via `st.chat_message`.
for message in st.session_state.messages:
    role = "assistant" if message["role"] == "model" else message["role"]
    with st.chat_message(role):
        st.markdown(message["content"])

# Create a chat input field to allow the user to enter a message.
if prompt := st.chat_input("What is up?"):

    # Store and display the current prompt.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Format history for Gemini chat API.
    chat_history = []
    for m in st.session_state.messages[:-1]: # exclude the latest user prompt
        gemini_role = "model" if m["role"] == "assistant" else "user"
        chat_history.append({
            "role": gemini_role,
            "parts": [{"text": m["content"]}]
        })

    # Generate a streaming response using the Gemini API.
    with st.chat_message("assistant"):
        try:
            # Start a chat session with history
            chat = client.chats.create(
                model="gemini-3.8-flash",
                history=chat_history
            )
            
            # Send the new message with streaming enabled
            response_stream = chat.send_message_stream(prompt)
            
            # Stream the response to the chat using `st.write_stream`
            def stream_generator():
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text

            response = st.write_stream(stream_generator())
            
            # Store the response in session state with role 'model'
            st.session_state.messages.append({"role": "model", "content": response})

        except Exception as e:
            st.error(f"An error occurred: {e}")
