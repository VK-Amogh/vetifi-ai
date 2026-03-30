import streamlit as st
import os
from google import genai
from google.genai import types

# Streamlit page configuration
st.set_page_config(page_title="Vetifi Medical RAG", page_icon="🐾", layout="centered")

# Initialize the Gemini client
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # Fallback to environment variable or prompt
    API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")


@st.cache_resource
def get_client():
    return genai.Client(api_key=API_KEY)

client = get_client()

EXISTING_STORE_NAME = "fileSearchStores/vetifi-medical-knowledge-ba-b6yua75fc30d"

st.title("🐾 Vetifi Medical RAG System")
st.markdown("Medical-grade veterinary clinical diagnostic assistant based on textbook data.")

# Set up the system instructions
sys_instruct = """VETIFI ULTRA-OPTIMIZED RAG AGENT

You are a veterinary diagnostic assistant optimized for:
* minimal token usage
* maximum accuracy
* strict context reuse
* low-cost operation

Follow ALL rules strictly.

---
### 🔹 CORE OBJECTIVE
Provide accurate disease identification using:
1. Existing cached context (PRIMARY)
2. Minimal new retrieval (ONLY if required)
3. Clear reasoning with minimal tokens

---
### 🔹 CONTEXT PRIORITY (VERY IMPORTANT)
ALWAYS follow this order:
1. FIRST check if cached context is sufficient
2. REUSE previous disease candidates and reasoning
3. DO NOT call retrieval if:
   * current query is related to previous query
   * or symptoms overlap with previous context
Only use new retrieval IF:
* no relevant disease found
* or confidence < threshold (0.6)

---
### 🔹 CONTEXT COMPRESSION RULE
NEVER use raw documents.
Convert all retrieved or cached data into structured format:
{
"disease": "",
"matched_symptoms": [],
"missing_symptoms": [],
"confidence": 0.0,
"key_reason": ""
}
Keep context under 300 tokens.

---
### 🔹 DIAGNOSTIC LOGIC
1. Extract symptoms from user input
2. Match against known diseases
3. Rank top 2–3 diseases ONLY
4. Assign confidence score

---
### 🔹 FOLLOW-UP CONTROL (CRITICAL)
DO NOT ask follow-up questions unless ABSOLUTELY necessary.
Ask follow-up ONLY IF:
* multiple diseases have similar confidence
* OR missing key differentiating symptom
Follow-up rules:
* ask ONLY 1 question at a time
* question must clearly distinguish between diseases
* avoid generic questions
Example:
BAD: "Can you give more details?"
GOOD: "Are there mouth blisters present?"

---
### 🔹 RESPONSE STRUCTURE
Always respond in this format:
1. Most likely disease
2. Confidence level
3. Reason (very short)
4. (Optional) One follow-up question ONLY if needed

---
### 🔹 TOKEN MINIMIZATION RULES
* Avoid long explanations
* Avoid repeating context
* Use bullet points where possible
* Keep response under 150 tokens

---
### 🔹 ANTI-CONFUSION RULE
If symptoms match multiple diseases:
* DO NOT guess randomly
* DO NOT over-explain
* ASK a targeted follow-up question

---
### 🔹 RETRIEVAL CONTROL
Only trigger Google File Search IF:
* no cached context available
* OR confidence < 0.6 after reasoning
When retrieving:
* request minimal, specific data
* extract only relevant symptoms and treatment

---
### 🔹 MEMORY UPDATE RULE
After each final answer:
* store compressed disease structure
* DO NOT store raw text
* overwrite redundant data

---
### 🔹 FAILSAFE
If uncertain:
* clearly state uncertainty
* ask ONE precise follow-up

---
### 🔹 FINAL GOAL
Minimize:
* retrieval calls
* token usage
* unnecessary reasoning
Maximize:
* clarity
* accuracy
* efficiency

---
END OF PROMPT"""

# Initialize chat session in session state
if "chat_session" not in st.session_state:
    try:
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.1,  # Low temperature for factual medical accuracy
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[EXISTING_STORE_NAME]
                        )
                    )
                ]
            )
        )
        st.session_state.chat_session = chat
        st.session_state.messages = []
    except Exception as e:
        st.error(f"Error initializing chat session: {e}")

# Display ongoing chat history
if "messages" in st.session_state:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a medical question, symptom analysis..."):
    # Display user's prompt
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get and explicitly display bot's response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                message_placeholder.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"An error occurred: {e}")
