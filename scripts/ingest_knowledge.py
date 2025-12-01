import os
import glob
import argparse
from typing import List, Dict
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
import tiktoken
import time

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ai-support-n8n', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded environment from {env_path}")
else:
    load_dotenv() # Fallback to default
    print("Loaded environment from default location")

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "urban-threads"

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    print("Error: OPENAI_API_KEY and PINECONE_API_KEY must be set in .env file")
    exit(1)

# Initialize clients
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

def get_embedding(text: str, model="text-embedding-3-small") -> List[float]:
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model, dimensions=512).data[0].embedding

def process_file(filepath: str) -> Dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    filename = os.path.basename(filepath)
    # Assume filename format: category_topic.txt or just topic.txt in a category folder
    # For this script, we'll assume the parent folder name is the namespace/category
    category = os.path.basename(os.path.dirname(filepath))
    
    # Valid namespaces based on router.json
    valid_namespaces = ['refunds', 'withdrawals', 'shipping', 'returns', 'billing', 'account']
    
    namespace = 'general'
    if category in valid_namespaces:
        namespace = category
    else:
        # Try to infer from filename
        name_lower = filename.lower()
        if 'account' in name_lower: namespace = 'account'
        elif 'billing' in name_lower or 'payment' in name_lower: namespace = 'billing'
        elif 'return' in name_lower: namespace = 'returns'
        elif 'shipping' in name_lower or 'tracking' in name_lower or 'order' in name_lower: namespace = 'shipping'
        elif 'refund' in name_lower: namespace = 'refunds'
        elif 'withdrawal' in name_lower: namespace = 'withdrawals'
    
    return {
        "id": filename,
        "text": content,
        "metadata": {
            "filename": filename,
            "category": category,
            "text": content
        },
        "namespace": namespace
    }

def ingest_directory(directory: str):
    print(f"Scanning directory: {directory}")
    files = glob.glob(os.path.join(directory, "**/*.txt"), recursive=True)
    files.extend(glob.glob(os.path.join(directory, "**/*.md"), recursive=True))
    
    print(f"Found {len(files)} files.")
    
    for filepath in files:
        print(f"Processing {filepath}...")
        try:
            data = process_file(filepath)
            vector = get_embedding(data['text'])
            
            # Upsert to Pinecone
            index.upsert(
                vectors=[{
                    "id": data['id'],
                    "values": vector,
                    "metadata": data['metadata']
                }],
                namespace=data['namespace']
            )
            print(f"Successfully ingested {data['id']} into namespace '{data['namespace']}'")
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest knowledge base into Pinecone")
    parser.add_argument("directory", help="Path to the knowledge base directory")
    args = parser.parse_args()
    
    ingest_directory(args.directory)
