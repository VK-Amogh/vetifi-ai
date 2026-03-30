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

PDF_PATH = r"d:\Internship\Vetifi\api search\single merged pdf circulatory sys.pdf"

def setup_rag_system():
    print("Creating File Search Store...")
    file_search_store = client.file_search_stores.create(
        config={'display_name': 'Vetifi Medical Knowledge Base'}
    )
    print(f"File search store created! Name: {file_search_store.name}")

    print(f"Uploading file to search store with custom chunking config...")
    operation = client.file_search_stores.upload_to_file_search_store(
        file_search_store_name=file_search_store.name,
        file=PDF_PATH,
        config={
            'chunking_config': {
              'white_space_config': {
                'max_tokens_per_chunk': 500,  # Larger chunks for better medical context
                'max_overlap_tokens': 50
              }
            }
        }
    )

    print("Waiting for chunking and indexing operation to complete...")
    while not operation.done:
        time.sleep(5)
        # Retrieve the updated operation status
        operation = client.operations.get(operation)
        print(".", end="", flush=True)

    print("\nCustom chunking and setup complete!")
    return file_search_store.name

# Set this to your existing store name to skip the 3-minute indexing phase.
# Set to None if you ever need to process a new PDF and create a new store.
EXISTING_STORE_NAME = "fileSearchStores/vetifi-medical-knowledge-ba-b6yua75fc30d"

def main():
    if not os.path.exists(PDF_PATH):
        print(f"Error: Could not find the PDF file at {PDF_PATH}")
        return

    print("=== Initializing Vetifi Medical RAG System ===")
    try:
        if EXISTING_STORE_NAME:
            print(f"[Optimized] Reusing existing File Search Store: {EXISTING_STORE_NAME}")
            store_name = EXISTING_STORE_NAME
        else:
            store_name = setup_rag_system()
    except Exception as e:
        print(f"Error during setup: {e}")
        return
    
    # Clear terminal for a clean interface
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(f"{Colors.CYAN}{Colors.BOLD}=== Vetifi Medical RAG System ==={Colors.ENDC}\n")
    print(f"{Colors.GREEN}System Ready.{Colors.ENDC} You can now ask medical questions, symptom analyses, and disease detection questions.")
    print(f"Type {Colors.WARNING}'quit'{Colors.ENDC} or {Colors.WARNING}'exit'{Colors.ENDC} to stop.\n")
    print("-" * 60)

    # Medical-grade system instructions to enforce strict textbook adherence and clinical tone
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
