import faiss
import pickle
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import dotenv_values
import chromadb
import argparse
import yaml

# Load environment variables from .env
config_db = dotenv_values("C:\\Users\\LAXMIKANT\\OneDrive\\Desktop\\Projects\\MLOPS\\SQL_Copilot\\.env")

def read_param(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
        return config

# Load metadata from pickle
def load_metadata_from_pickle(metadata_path):
    with open(metadata_path, "rb") as f:
        metadata = pickle.load(f)
    print(f"📄 Loaded {len(metadata)} metadata entries from {metadata_path}")
    return metadata

def retrieve_from_faiss(query, config, top_k):

    # Get FAISS db
    index = faiss.read_index(config["vector_store"]["path_to_save"])

    # Get metadata
    metadata = load_metadata_from_pickle(config["vector_store"]["metadata_path"])

    # Load the Embedding model
    model = SentenceTransformer(config["embedding_model"])
    query_vector = model.encode([query])

    # Query the database
    distances, indices = index.search(np.array(query_vector), top_k)
    results = [
        {**metadata[i], "similarity_score": float(distances[0][idx])}
        for idx, i in enumerate(indices[0])
    ]
    return results

def retrieve_from_pinecone(query, config, top_k):
    # Pinecone API details
    api_key = config_db.get("PINECONE_API_KEY")

    # Vector store config
    index_name = config["vector_store"]["index_name"]
    namespace = config["vector_store"]["namespace"]
    metadata_path = config["vector_store"]["metadata_path"]

    # Initialize Pinecone client
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)

    # Load embedding model
    model = SentenceTransformer(config["embedding_model"])
    query_vector = model.encode([query])[0].tolist()

    # Query Pinecone
    response = index.query(
        vector=query_vector,
        top_k=top_k,
        include=["metadata", "score"],
        namespace=namespace
    )

    # Load metadata
    full_metadata = load_metadata_from_pickle(metadata_path)

    # Format output like FAISS
    results = []
    for match in response['matches']:
        idx = int(match['id'].split('-')[-1])
        item_metadata = full_metadata[idx]
        item_metadata["similarity_score"] = match["score"]
        results.append(item_metadata)

    return results

def retrieve_from_chromadb(query, config, top_k):
    # 1. Load metadata from pickle path
    metadata_path = config["vector_store"]["metadata_path"]
    metadata = load_metadata_from_pickle(metadata_path)

    # 2. Load embedding model
    model = SentenceTransformer(config["embedding_model"])
    query_vector = model.encode([query])[0]  # Shape: (dim,)

    # 3. Connect to ChromaDB
    persist_dir = config["vector_store"]["persist_directory"]
    collection_name = config["vector_store"]["collection_name_chroma"]
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_collection(name=collection_name)

    # 4. Query Chroma
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        include=["metadatas", "distances"]
    )

    # 5. Construct result similar to FAISS format
    retrieved_results = []
    for i, distance in zip(results["ids"][0], results["distances"][0]):
        index = int(i.split("_")[1])
        data = metadata[index]
        data["similarity_score"] = float(distance)
        retrieved_results.append(data)

    return retrieved_results

def get_similar_context(query, config_path="params.yaml", top_k=None):
    config = read_param(config_path)
    store_type = config["vector_store"]["type"].lower()

    if top_k is None:
        top_k = config["vector_store"]["top_k"]

    if store_type == "faiss":
        return retrieve_from_faiss(query, config, top_k)
    elif store_type == "pinecone":
        return retrieve_from_pinecone(query, config, top_k)
    elif store_type == "chromadb":
        return retrieve_from_chromadb(query, config, top_k)
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="params.yaml")
    parsed_args = parser.parse_args()

    query = "Get me all data from Table"
    results = get_similar_context(query=query, config_path=parsed_args.config, top_k=5)

    if not results:
        print("⚠️ No results found.")
    else:
        print("✅ Top results:\n")
        print(results,"\n\n")