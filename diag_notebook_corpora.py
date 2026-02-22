import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

def verify_corpora_access():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        return

    genai.configure(api_key=api_key)

    print("--- Searching for NotebookLM Corpora (Vertex AI / Enterprise) ---")
    try:
        # The list_corpora method exists in the latest GenAI SDK for Enterprise grounding
        corpora = genai.list_corpora()
        found = False
        for corpus in corpora:
            print(f"Corpus: {corpus.name} | Display Name: {corpus.display_name}")
            if "veraguard_intel" in corpus.display_name.lower() or "veraguard_intel" in corpus.name.lower():
                found = True
                print(f"\n[BRIDGE] Found target intelligence corpus: {corpus.display_name}")
                # List documents in this corpus
                docs = genai.list_documents(corpus_name=corpus.name)
                doc_list = list(docs)
                print(f"[BRIDGE] Source Count: {len(doc_list)}")
                for doc in doc_list[:10]:
                    print(f"  - {doc.display_name}")
        
        if not found:
            print("No corpus matching 'VeraGuard_Intel' found via AI SDK.")
            
    except Exception as e:
        print(f"Error accessing Corpora API: {e}")
        print("\nNote: This requires an AI Studio or Vertex AI key with Semantic Retriever permissions enabled.")

if __name__ == "__main__":
    verify_corpora_access()
