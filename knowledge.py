import os
import chromadb
from chromadb.utils import embedding_functions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from config import KNOWLEDGE_DIR, DB_DIR

# 1. Setup a lightweight pipeline (NO OCR)
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False  # This prevents the 'bad_alloc' error
pipeline_options.do_table_structure = True 

# 2. Initialize ChromaDB
default_ef = embedding_functions.DefaultEmbeddingFunction()
client = chromadb.PersistentClient(path=DB_DIR)
collection = client.get_or_create_collection(name="assistant_knowledge", embedding_function=default_ef)

def chunk_text(text, chunk_size=1000, overlap=150):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def sync_knowledge(force_rebuild=False):
    print(f"\n--- ⚡ Fast-Track Knowledge Indexing (No OCR) ---")
    
    # Use the lightweight options here
    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    files = [f for f in os.listdir(KNOWLEDGE_DIR) if f.endswith('.pdf')]
    for file_name in files:
        print(f"📄 Extracting Text: {file_name}...")
        try:
            result = converter.convert(os.path.join(KNOWLEDGE_DIR, file_name))
            full_text = result.document.export_to_markdown()
            
            text_chunks = chunk_text(full_text)
            for i, chunk in enumerate(text_chunks):
                collection.upsert(documents=[chunk], ids=[f"{file_name}_{i}"])
            print(f"✅ Successfully indexed {len(text_chunks)} chunks.")
        except Exception as e:
            print(f"❌ Error on {file_name}: {e}")

def query_knowledge(query_text, n_results=3):
    try:
        results = collection.query(query_texts=[query_text], n_results=n_results)
        if results and results['documents'] and results['documents'][0]:
            context = "\n\n---\n\n".join(results['documents'][0])
            print(f"🔍 [DEBUG] Retrieved {len(context)} chars for LLM.")
            return context, 0.95
    except Exception as e:
        print(f"⚠️ Error: {e}")
    return "", 0.0

build_index = sync_knowledge
get_relevant_context = query_knowledge

if __name__ == "__main__":
    sync_knowledge()