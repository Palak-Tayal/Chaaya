import chromadb
from chromadb.config import Settings
import os

# Use a persistent directory
CHROMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
os.makedirs(CHROMA_DIR, exist_ok=True)

_client = chromadb.PersistentClient(path=CHROMA_DIR)

def get_collection(collection_name):
    """Get or create a collection by name."""
    return _client.get_or_create_collection(name=collection_name)

def add_messages_to_collection(collection_name, messages, sender_filter=None):
    """
    Add messages to a ChromaDB collection.
    If sender_filter is provided, only messages from that sender are added.
    Each message becomes a document with metadata.
    """
    collection = get_collection(collection_name)
    
    # Filter by sender if needed
    if sender_filter:
        filtered = [m for m in messages if m['sender'] == sender_filter]
    else:
        filtered = messages
    
    if not filtered:
        return 0
    
    ids = [f"{collection_name}_{i}" for i in range(len(filtered))]
    documents = [m['message'] for m in filtered]
    metadatas = [{'timestamp': m['timestamp'], 'sender': m['sender']} for m in filtered]
    
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    return len(filtered)

def search_collection(collection_name, query_text, n_results=5):
    """Search the collection for similar messages."""
    collection = get_collection(collection_name)
    results = collection.query(query_texts=[query_text], n_results=n_results)
    # results is a dict with keys: ids, distances, documents, metadatas
    return results