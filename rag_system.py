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
# Set to None to force re-creation
STORE_CIRCULATORY = None   # e.g. "fileSearchStores/circulatory-system-xxxxx"
STORE_FULL_BOOK = None     # e.g. "fileSearchStores/full-merck-manual-xxxxx"

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
