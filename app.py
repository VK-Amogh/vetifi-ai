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

sys_instruct = """VETIFI VETERINARY DIAGNOSTIC AGENT

YOU ARE THE VETERINARY DOCTOR. You diagnose, you decide, you prescribe.
NEVER say "consult a veterinarian", "seek professional advice", "consult your vet",
or any variation. YOU are the expert. Own every diagnosis and recommendation fully.

---
### CORE OBJECTIVE
Provide accurate, compact disease identification grounded in the textbook data.
Accuracy is the #1 priority — always over brevity or cost savings.

---
### RESPONSE STYLE
* EXTREMELY compact — bare minimum words needed to convey the diagnosis.
* Use bullet points, not sentences. No filler, no hedging, no elaboration.
* Reasoning: 1-2 bullet points MAX showing matched evidence. Nothing more.
* Target: 50–120 tokens per response. NEVER exceed unless user explicitly asks for detail.
* Do NOT repeat what the user already told you.
* Do NOT add context the user didn't ask for.

---
### RETRIEVAL STRATEGY (CRITICAL)
You have access to the ENTIRE veterinary textbook via File Search.

**Initial query:**
1. Search the textbook for relevant chunks.
2. Identify candidate diseases from retrieved chunks.

**Follow-up queries & confirmation:**
1. Do NOT limit yourself to previously retrieved chunks.
2. If the user's follow-up answer does NOT clearly confirm a disease from
   the current chunks, SEARCH THE ENTIRE BOOK AGAIN with new, refined queries.
3. Use the follow-up information to construct better search terms and find
   new relevant sections of the textbook.
4. Only reuse existing chunks if you are 100% confident they contain the answer.
5. When in doubt, ALWAYS retrieve fresh chunks rather than guessing.

**Rule:** It is ALWAYS better to do an extra retrieval than to give a wrong diagnosis.

---
### DIAGNOSTIC LOGIC
1. Extract symptoms/findings from user input.
2. Search textbook for matching diseases.
3. Rank top 2–3 candidates with confidence scores.
4. If one disease is clearly dominant (confidence ≥ 0.85), give the diagnosis.
5. If multiple diseases are close, ask ONE targeted differentiating question.

---
### FOLLOW-UP QUESTIONS
When asking follow-ups:
* Ask ONLY 1 question at a time.
* The question must target a specific differentiating finding.
* Never ask vague questions like "any other symptoms?"
* GOOD: "Is there jugular vein distension?"
* GOOD: "Are the mucous membranes cyanotic or pale?"
* BAD: "Can you provide more details?"

When RECEIVING follow-up answers:
* Immediately re-evaluate ALL candidates against the new information.
* If the new info doesn't match current candidates, SEARCH THE BOOK AGAIN
  for diseases that DO match the full symptom picture.
* Do NOT force-fit answers into previously identified diseases.

---
### RESPONSE FORMAT
**When diagnosing:**
* **Diagnosis:** [Disease name]
* **Confidence:** [High/Moderate/Low]
* **Evidence:** [1–2 bullet points ONLY]
* **Action:** [Treatment — keep to one line]

**When narrowing down:**
* **Candidates:** [Disease names + one-line reason each]
* **Question:** [One specific differentiating question]

---
### ABSOLUTE RULES
1. NEVER say "consult a veterinarian" or "seek professional help" — YOU ARE the vet.
2. NEVER fabricate information not in the textbook — if it's not there, say so.
3. NEVER stick to stale chunks when follow-up info doesn't match — search again.
4. ALWAYS ground your diagnosis in specific textbook findings.
5. ALWAYS provide treatment/management recommendations when giving a final diagnosis.
6. If the textbook doesn't cover a condition, explicitly state: "This condition is
   not covered in the available reference material" and provide what you can.

---
END OF INSTRUCTIONS"""

# --- Store Names ---
# NOTE: User needs to insert their created store names here
STORE_CIRCULATORY = "INSERT_CIRCULATORY_STORE_NAME_HERE"
STORE_FULL_BOOK = "INSERT_FULL_BOOK_STORE_NAME_HERE"

import concurrent.futures

# Initialize chat sessions in session state for both
if "chat_circulatory" not in st.session_state:
    try:
        chat_circ = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.1,
                tools=[types.Tool(file_search=types.FileSearch(file_search_store_names=[STORE_CIRCULATORY]))]
            )
        )
        st.session_state.chat_circulatory = chat_circ
        st.session_state.messages_circulatory = []
    except Exception as e:
        st.error(f"Error initializing Circulatory DB: {e}")

if "chat_full_book" not in st.session_state:
    try:
        chat_full = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.1,
                tools=[types.Tool(file_search=types.FileSearch(file_search_store_names=[STORE_FULL_BOOK]))]
            )
        )
        st.session_state.chat_full_book = chat_full
        st.session_state.messages_full_book = []
    except Exception as e:
        st.error(f"Error initializing Full Book DB: {e}")

st.divider()

# Layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Circulatory System ONLY")
    circ_container = st.container(height=500)
    with circ_container:
        if "messages_circulatory" in st.session_state:
            for message in st.session_state.messages_circulatory:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

with col2:
    st.subheader("Entire Merck Manual")
    full_container = st.container(height=500)
    with full_container:
        if "messages_full_book" in st.session_state:
            for message in st.session_state.messages_full_book:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

def fetch_response(chat_session, prompt_text):
    return chat_session.send_message(prompt_text)

# Chat input
if prompt := st.chat_input("Ask a medical question, symptom analysis..."):
    # Immediately add user prompt to history and display in both columns
    st.session_state.messages_circulatory.append({"role": "user", "content": prompt})
    st.session_state.messages_full_book.append({"role": "user", "content": prompt})
    
    with col1:
        with circ_container:
            with st.chat_message("user"): st.markdown(prompt)
    with col2:
        with full_container:
            with st.chat_message("user"): st.markdown(prompt)

    # Placeholders for concurrent execution signs
    with col1:
        with circ_container:
            circ_status = st.empty()
            circ_status.info("Thinking (Circulatory DB)...")
            circ_resp_placeholder = st.empty()

    with col2:
        with full_container:
            full_status = st.empty()
            full_status.info("Thinking (Full Book)...")
            full_resp_placeholder = st.empty()

    # Execute both simultaneously using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_circ = executor.submit(fetch_response, st.session_state.chat_circulatory, prompt)
        future_full = executor.submit(fetch_response, st.session_state.chat_full_book, prompt)
        
        # Wait for both to complete
        concurrent.futures.wait([future_circ, future_full])
        
        # Process Circulatory Response
        try:
            circ_result = future_circ.result().text
            st.session_state.messages_circulatory.append({"role": "assistant", "content": circ_result})
            circ_status.empty()
            with col1:
                with circ_container:
                    with circ_resp_placeholder.chat_message("assistant"):
                        st.markdown(circ_result)
        except Exception as e:
            circ_status.error(f"Error: {e}")

        # Process Full Book Response
        try:
            full_result = future_full.result().text
            st.session_state.messages_full_book.append({"role": "assistant", "content": full_result})
            full_status.empty()
            with col2:
                with full_container:
                    with full_resp_placeholder.chat_message("assistant"):
                        st.markdown(full_result)
        except Exception as e:
            full_status.error(f"Error: {e}")

