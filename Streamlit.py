import streamlit as st
from TravelOrganizerLLM import askLLMPriority

# Initialize the list of messages in the session, if not already present
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Where do you need to go on mission?", "avatar": "✈️"}
    ]

# Display all stored messages
for message in st.session_state.messages:
    message_class = "assistant" if message["role"] == "assistant" else "user"
    with st.chat_message(message["role"], avatar=message.get("avatar", "")):
        st.markdown(
            f"<div class='chat-message {message_class}'>{message['content']}</div>",
            unsafe_allow_html=True,
        )

# Handle user input
if prompt := st.chat_input("e.g., Fastest flight from Geneva to Valencia for tomorrow"):
    # Immediately add the user's message to the conversation
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "👤"})

    # Immediately display the user's message
    with st.chat_message("user", avatar="👤"):
        st.markdown(
            f"<div class='chat-message user'>{prompt}</div>",
            unsafe_allow_html=True,
        )

    # Show a spinner while processing the response
    with st.spinner("Operation in progress. Please wait..."):
        # Call the function to get the response
        response = askLLMPriority(prompt)

    # Add the assistant's response to the list of messages
    st.session_state.messages.append({"role": "assistant", "content": response, "avatar": "✈️"})

    # Immediately display the assistant's response
    with st.chat_message("assistant", avatar="✈️"):
        st.markdown(
            f"<div class='chat-message assistant'>{response}</div>",
            unsafe_allow_html=True,
        )
