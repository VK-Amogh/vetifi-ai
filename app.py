import streamlit as st
import os
import time
from google import genai
from google.genai import types

# --- Page config ---
st.set_page_config(page_title="Vetifi AI", page_icon="🐾", layout="centered")

# --- API Key ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = os.environ.get("GEMINI_API_KEY", "")

@st.cache_resource
def get_client():
    return genai.Client(api_key=API_KEY)

client = get_client()

# --- Circulatory System Store ONLY ---
STORE = "fileSearchStores/vetifi-circulatory-db-hu6b2ley5ac8"

# --- System Instructions ---
sys_instruct = """VETIFI VETERINARY DIAGNOSTIC AGENT

YOU ARE THE VETERINARY DOCTOR. You diagnose, you decide, you prescribe.
NEVER say "consult a veterinarian", "seek professional advice", "consult your vet",
or any variation. YOU are the expert. Own every diagnosis and recommendation fully.

---
### CORE OBJECTIVE
Provide accurate, compact disease identification grounded in the textbook data.
Accuracy is the #1 priority.

---
### RESPONSE STYLE
* EXTREMELY compact — bare minimum words needed to convey the diagnosis.
* Use bullet points, not sentences. No filler, no hedging, no elaboration.
* Reasoning: 1-2 bullet points MAX showing matched evidence. Nothing more.
* Target: 50-120 tokens per response. NEVER exceed unless user explicitly asks for detail.
* Do NOT repeat what the user already told you.
* Do NOT add context the user didn't ask for.

---
### RETRIEVAL STRATEGY (CRITICAL)
You have access to the circulatory system veterinary textbook via File Search.

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
3. Rank top 2-3 candidates with confidence scores.
4. If one disease is clearly dominant (confidence >= 0.85), give the diagnosis.
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
* If the new info doesn't match current candidates, SEARCH THE BOOK AGAIN.
* Do NOT force-fit answers into previously identified diseases.

---
### RESPONSE FORMAT
**When diagnosing:**
* **Diagnosis:** [Disease name]
* **Confidence:** [X%] — e.g. 87%
* **Evidence:** [1-2 bullet points ONLY]
* **Action:** [Treatment - keep to one line]

**When narrowing down:**
* **Candidates:** [Disease name — X% confidence, one-line reason each]
* **Question:** [One specific differentiating question]

---
### ABSOLUTE RULES
1. NEVER say "consult a veterinarian" or "seek professional help" - YOU ARE the vet.
2. NEVER fabricate information not in the textbook - if it's not there, say so.
3. NEVER stick to stale chunks when follow-up info doesn't match - search again.
4. ALWAYS ground your diagnosis in specific textbook findings.
5. ALWAYS provide treatment/management recommendations when giving a final diagnosis.

---
END OF INSTRUCTIONS"""

# --- Initialize chat session ---
if "chat" not in st.session_state:
    try:
        st.session_state.chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                temperature=0.1,
                tools=[types.Tool(file_search=types.FileSearch(file_search_store_names=[STORE]))]
            )
        )
        st.session_state.messages = []
    except Exception as e:
        st.error(f"Error initializing Vetifi: {e}")

# --- UI ---
st.title("🐾 Vetifi AI")
st.markdown("Veterinary diagnostic assistant — Merck Manual Circulatory System")
st.divider()

# Display chat history
if "messages" in st.session_state:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Describe symptoms or ask a diagnostic question..."):
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        with st.spinner("Thinking..."):
            for attempt in range(3):
                try:
                    response = st.session_state.chat.send_message(prompt)
                    placeholder.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    break
                except Exception as e:
                    err = str(e)
                    if ("429" in err or "RESOURCE_EXHAUSTED" in err) and attempt < 2:
                        wait = 60 if attempt == 0 else 120  # 60s then 120s
                        placeholder.warning(f"⏳ Quota limit hit — waiting {wait}s before retry (attempt {attempt+1}/3)...")
                        time.sleep(wait)
                        continue
                    placeholder.error(f"Error: {e}")
                    break
