import streamlit as st
from google import genai

# Show title and description.
st.title("💬 Gemini Chatbot")
st.write(
    "This is a simple chatbot that uses Google's Gemini model to generate responses. "
    "To use this app, you need to provide a Gemini API key."
)

# Ask user for their Gemini API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it via `st.secrets`.
gemini_api_key = st.text_input("Gemini API Key", type="password")

if not gemini_api_key:
    st.info("Please add your Gemini API key to continue.", icon="🗝️")
else:
    # Create a Gemini client.
    client = genai.Client(api_key=gemini_api_key)

    # Create a session state variable to store the chat messages.
    # Note: Gemini uses 'model' instead of 'assistant' for the model role.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        # Streamlit display uses 'assistant', but we map 'model' to 'assistant' for UI consistency if needed,
        # or just keep 'assistant'/'user' in session state and convert when sending to Gemini.
        role = "assistant" if message["role"] == "model" else message["role"]
        with st.chat_message(role):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message.
    if prompt := st.chat_input("What is up?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Format history for Gemini chat API (Gemini expects 'user' and 'model' roles).
        # We map st.session_state messages to the structure Gemini expects.
        chat_history = []
        for m in st.session_state.messages[:-1]: # exclude the latest user prompt
            # Map UI roles to Gemini roles
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
                    model="gemini-2.5-flash",
                    history=chat_history
                )
                
                # Send the new message with streaming enabled
                response_stream = chat.send_message(prompt, stream=True)
                
                # Stream the response to the chat using `st.write_stream`
                # Note: We create a generator that yields text chunks from the Gemini stream.
                def stream_generator():
                    for chunk in response_stream:
                        if chunk.text:
                            yield chunk.text

                response = st.write_stream(stream_generator())
                
                # Store the response in session state with role 'model' (Gemini's role)
                st.session_state.messages.append({"role": "model", "content": response})

            except Exception as e:
                st.error(f"An error occurred: {e}")
