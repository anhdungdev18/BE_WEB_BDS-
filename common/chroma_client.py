# common/chroma_client.py
import chromadb

_client = None

def get_chroma_client():
    global _client
    if _client is None:
        # Huynh có thể đổi path nếu muốn
        _client = chromadb.PersistentClient(path="./chroma_db")
    return _client

def get_listings_collection():
    client = get_chroma_client()
    # Tên collection tuỳ huynh
    return client.get_or_create_collection("bds_listings")
