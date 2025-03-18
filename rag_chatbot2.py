import streamlit as st
import requests
import json
import sseclient
from datetime import datetime

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = None

# App layout
st.title("Digital China RAG Chatbot")
st.markdown("### Welcome to Digital China Knowledge Assistant")
st.markdown("""
Please enter your inquiry regarding:
- Internal Employee SOP 
- Digital Project Experience Sharing
- Lessons Learned for Project EMS
""")

# API Configuration
BASE_URL = "https://api.dify.ai/v1"
api_key = "app-py7xeI5OV3BcdJZ2iO5PF8zb"  # Replace with your API key

# Input Parameters
col1, col2 = st.columns(2)
with col1:
    output_style = st.selectbox("Output Style", ["Detailed", "Concise", "Normal"])
with col2:
    query_field = st.selectbox("Query Field", ["Employee SOP", "Digital Project Experience", "General Inquiry"])

def send_chat_message(query):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    inputs = {
        "Output_style": output_style,
        "Query_field": query_field
    }

    # Combine parameters with user query
    full_query = f"{query_field}: {query} ({output_style} response requested)"
    
    payload = {
        "inputs": inputs,
        "query": full_query,  # Send combined query
        "response_mode": "streaming",
        "conversation_id": st.session_state.conversation_id or "",
        "user": "digital-china-user",
        "auto_generate_name": True
    }
    
    response = requests.post(
        f"{BASE_URL}/chat-messages",
        headers=headers,
        json=payload,
        stream=True
    )
    return response

def handle_stream_response(response):
    client = sseclient.SSEClient(response)
    full_answer = ""
    
    with st.chat_message("assistant"):
        answer_placeholder = st.empty()
        temp_answer = ""
        
        for event in client.events():
            if event.data:
                data = json.loads(event.data)
                if data.get('event') == 'message':
                    temp_answer += data.get('answer', '')
                    answer_placeholder.markdown(temp_answer + "▌")
                
                if data.get('event') == 'message_end':
                    full_answer = temp_answer
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": full_answer,
                        "message_id": data.get('message_id'),
                        "timestamp": datetime.now().isoformat()
                    })
                    st.session_state.conversation_id = data.get('conversation_id')
                    answer_placeholder.markdown(full_answer)
                    break

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Enter your question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.spinner("Processing..."):
        response = send_chat_message(prompt)
        if response.status_code == 200:
            handle_stream_response(response)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")