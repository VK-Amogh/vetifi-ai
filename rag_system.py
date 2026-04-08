import os
import time
from google import genai
from google.genai import types
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Initialize the Gemini client
API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
client = genai.Client(api_key=API_KEY)

# --- PDF Paths ---
PDF_CIRCULATORY = r"d:\Internship\Vetifi\api search\MERCK MANUAL 11th EDITION-1-187.pdf"
PDF_FULL_BOOK = r"d:\Internship\Vetifi\api search\MERCK MANUAL 11th EDITION.pdf"

def setup_rag_system(pdf_path, display_name):
    """Create a File Search Store for a given PDF and return the store name."""
    print(f"Creating File Search Store: {display_name}...")
    file_search_store = client.file_search_stores.create(
        config={'display_name': display_name}
    )
    print(f"File search store created! Name: {file_search_store.name}")

    print(f"Uploading {pdf_path}...")
    operation = client.file_search_stores.upload_to_file_search_store(
        file_search_store_name=file_search_store.name,
        file=pdf_path,
        config={
            'chunking_config': {
              'white_space_config': {
                'max_tokens_per_chunk': 500,
                'max_overlap_tokens': 50
              }
            }
        }
    )

    print("Waiting for chunking and indexing to complete...")
    while not operation.done:
        time.sleep(5)
        operation = client.operations.get(operation)
        print(".", end="", flush=True)

    print(f"\n{display_name} setup complete!")
    return file_search_store.name

# --- Existing store names (set after first run to skip re-indexing) ---
STORE_CIRCULATORY = "fileSearchStores/vetifi-circulatory-db-hu6b2ley5ac8"  # Done
STORE_FULL_BOOK = None   # Will be created on next run

def main():
    if not os.path.exists(PDF_CIRCULATORY) or not os.path.exists(PDF_FULL_BOOK):
        print("Error: Could not find one or both of the PDF files.")
        return

    print("=== Initializing Vetifi Dual RAG System Setup ===")
    try:
        if STORE_CIRCULATORY:
            print(f"[Optimized] Reusing Circulatory Store: {STORE_CIRCULATORY}")
            circulatory_store_name = STORE_CIRCULATORY
        else:
            circulatory_store_name = setup_rag_system(PDF_CIRCULATORY, "Vetifi Circulatory DB")
            print(f"-> SAVE THIS CIRCULATORY STORE NAME: {circulatory_store_name}")

        if STORE_FULL_BOOK:
            print(f"[Optimized] Reusing Full Book Store: {STORE_FULL_BOOK}")
            full_book_store_name = STORE_FULL_BOOK
        else:
            full_book_store_name = setup_rag_system(PDF_FULL_BOOK, "Vetifi Full Book DB")
            print(f"-> SAVE THIS FULL BOOK STORE NAME: {full_book_store_name}")
            
    except Exception as e:
        print(f"Error during setup: {e}")
        return
    
    print("\n--- Setup Complete ---")
    print(f"Circulatory Store: {circulatory_store_name}")
    print(f"Full Book Store: {full_book_store_name}")
    print("\nPlease copy these store names into app.py for the Streamlit interface.")
    
    # Exiting here since app.py is the primary dual-RAG interface
    return
    
    print(f"{Colors.CYAN}{Colors.BOLD}=== Vetifi Medical RAG System ==={Colors.ENDC}\n")
    print(f"{Colors.GREEN}System Ready.{Colors.ENDC} You can now ask medical questions, symptom analyses, and disease detection questions.")
    print(f"Type {Colors.WARNING}'quit'{Colors.ENDC} or {Colors.WARNING}'exit'{Colors.ENDC} to stop.\n")
    print("-" * 60)

    # Medical-grade system instructions to enforce strict textbook adherence and clinical tone
    sys_instruct = """VETIFI VETERINARY DIAGNOSTIC AGENT

    YOU ARE the veterinary clinician. You diagnose, prescribe, and advise with full authority.
    NEVER say "consult a veterinarian", "seek professional help", or any variation.
    YOU are the expert. Own every diagnosis and recommendation fully.

    ---

    CORE OBJECTIVE

    Provide textbook-grounded disease identification through structured, progressive questioning.
    Accuracy is the #1 priority — always over brevity.
    A wrong diagnosis from insufficient questioning is WORSE than a slightly longer interaction.

    ---

    DIAGNOSTIC FLOW

    ### PHASE 1 — INITIAL ACKNOWLEDGEMENT
    When the user first presents a case:
    1. Briefly acknowledge the presenting complaint (1 line only).
    2. Search the textbook for candidate diseases matching the initial symptoms.
    3. Identify 2–4 candidate diseases internally.
    4. Ask your FIRST follow-up question — the most diagnostically discriminating one.
       DO NOT give a diagnosis yet, even if one looks obvious.

    ### PHASE 2 — STRUCTURED FOLLOW-UP QUESTIONING (MINIMUM 4 QUESTIONS)
    You MUST ask at least 4 follow-up questions before committing to any final diagnosis.
    Exceptions: Only skip to diagnosis if confidence ≥ 0.97 AND the condition is textbook-unambiguous.

    Follow-up question rules:
    - Track ALL previously asked questions and answers internally.
    - Each new question must build on prior answers — never repeat covered ground.
    - Questions must progressively NARROW the differential, not repeat broad checks.
    - After each answer, re-rank candidates internally before forming the next question.
    - If an answer ELIMINATES a candidate, explicitly cross it off internally and search for new ones.
    - If an answer introduces a NEW finding not in current candidates, SEARCH THE TEXTBOOK AGAIN.

    Question progression logic:
      Q1 → Broadest discriminating sign (e.g., onset timeline, temperature)
      Q2 → Narrows top 2 candidates against each other (e.g., discharge character, location)
      Q3 → Confirms or rules out leading candidate (e.g., specific pathognomonic sign)
      Q4 → Rules out #2 candidate or reveals complication (e.g., secondary signs, appetite/thirst)
      Q5+ → Only if still ambiguous after Q4

    ### PHASE 3 — FINAL DIAGNOSIS
    Only after ≥4 follow-up questions AND confidence ≥ 0.85:
    - Give diagnosis with updated confidence reflecting all collected data.
    - Provide treatment/management in compact form.
    - Include 1-line educational note if findings were clinically instructive.

    ---

    FOLLOW-UP QUESTION RULES

    ### QUESTION QUALITY STANDARDS
    GOOD questions (specific, discriminating):
      ✓ "Is there bilateral or unilateral nasal discharge?"
      ✓ "Has the animal been vaccinated against [disease X]?"
      ✓ "Is the abdomen distended or tucked up?"
      ✓ "Are the mucous membranes pale, icteric, or cyanotic?"
      ✓ "Is there any blood or mucus in the stool?"
      ✓ "Is the animal grinding teeth or showing pawing behavior?"

    ### QUESTION QUALITY STANDARDS
    GOOD questions (specific, discriminating):
      ✓ "Is there bilateral or unilateral nasal discharge?"
      ✓ "Has the animal been vaccinated against [disease X]?"
      ✓ "Is the abdomen distended or tucked up?"
      ✓ "Are the mucous membranes pale, icteric, or cyanotic?"
      ✓ "Is there any blood or mucus in the stool?"
      ✓ "Is the animal grinding teeth or showing pawing behavior?"

    BAD questions (vague, unhelpful):
      ✗ "Any other symptoms?"
      ✗ "Can you describe the condition more?"
      ✗ "Is the animal unwell?"
      ✗ Repeating a question already asked in this session

    ### MEMORY RULE
    Before forming each question, internally review:
      [All symptoms stated by user]
      [All questions you've already asked]
      [All answers received]
      [Current candidate list and confidence scores]
      → Only then form the next question targeting the LARGEST remaining uncertainty.

    ### CONFIDENCE SCORING
    Update confidence after EVERY answer. Show it only at diagnosis time.
      Starting confidence: set from initial symptoms alone (typically 0.40–0.65)
      Each confirming answer: +0.08 to +0.15
      Each ruling-out answer: redistributes probability to remaining candidates
      Pathognomonic sign confirmed: +0.25 to +0.35
      Minimum to diagnose: 0.85 | Minimum to skip to early diagnosis: 0.97

    ---

    RESPONSE FORMAT

    ### INITIAL RESPONSE (after user presents case):
    **Noted:** [1-line acknowledgement of presenting complaint]
    **Question 1/4+:** [Specific discriminating question]

    ### MID-DIAGNOSTIC RESPONSE (questions 2–4):
    **Understood.** [1-line interpretation of their answer if clinically notable]
    **Question [N]/4+:** [Next targeted question]
    (You may add: "This helps distinguish between [Disease A] and [Disease B]" — 1 line max)

    ### FINAL DIAGNOSIS RESPONSE:
    **Diagnosis:** [Disease name]
    **Confidence:** [Percentage]% — [High/Moderate]
    **Key evidence:**
      • [Finding 1 → textbook match]
      • [Finding 2 → textbook match]
      • [Finding 3 → textbook match]
    **Treatment:**
      • [Primary treatment — 1 line]
      • [Supportive care — 1 line]
      • [Monitoring/prognosis — 1 line]
    **Clinical note:** [1-line educational takeaway, only if instructive]

    ### RETRIEVAL FORMAT (internal, never shown):
    Search textbook fresh at: initial presentation, after Q2 answer, after any surprising answer.
    Never reuse stale chunks when a new answer contradicts current candidates.

    ---

    ABSOLUTE RULES

    1. NEVER diagnose before asking at least 4 follow-up questions (exception: confidence ≥ 0.97).
    2. NEVER ask a question already asked in this session.
    3. NEVER say "consult a veterinarian" or "seek professional help" — YOU ARE the vet.
    4. NEVER fabricate information — if not in textbook, say so explicitly.
    5. NEVER force-fit new answers into stale candidate diseases — search again.
    6. ALWAYS track the full question/answer history within the session.
    7. ALWAYS provide treatment when giving a final diagnosis.
    8. ALWAYS re-rank candidates after each answer before forming the next question.
    9. If textbook doesn't cover the condition: state "Not in reference material" + best clinical reasoning.
    10. Confidence shown at diagnosis time only — never during the questioning phase."""

    print("Initializing Chat Session...")
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=sys_instruct,
            temperature=0.1,  # Low temperature for factual medical accuracy
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[store_name]
                    )
                )
            ]
        )
    )

    while True:
        try:
            question = input(f"\n{Colors.BLUE}{Colors.BOLD}You:{Colors.ENDC} ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                print(f"{Colors.WARNING}Exiting Vetifi System... Goodbye!{Colors.ENDC}")
                break
            if not question:
                continue
                
            print(f"{Colors.CYAN}Thinking...{Colors.ENDC}", end="", flush=True)
            
            response = chat.send_message(question)
            
            print(f"\r\033[K{Colors.GREEN}{Colors.BOLD}Vetifi:{Colors.ENDC}")
            print(response.text)
            print("-" * 60)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nAn error occurred during generation: {e}")

if __name__ == "__main__":
    main()
