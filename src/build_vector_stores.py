import pandas as pd
import faiss
import chromadb # type:ignore
from pinecone import Pinecone, ServerlessSpec # type: ignore
from dotenv import dotenv_values
import pickle
from sentence_transformers import SentenceTransformer
import os
import argparse
import yaml

# Load environment variables from .env
config_db = dotenv_values("C:/Users/Pranita/Desktop/PROJECTS/MLOPS_PROJECT/.env")

# defination for reading YAML config
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

# dynamic embedding function
def get_embeddings(texts, model_name):
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

# building FAISS backend
def build_faiss_index(df,texts, embeddings, config):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    index_path = config["vector_store"]["path_to_save"]
    metadata_path = config["vector_store"]["metadata_path"]

    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    faiss.write_index(index, index_path)

    with open(metadata_path, "wb") as f:
        pickle.dump(df.to_dict("records"), f)

    print("FAISS vector store and metadata saved.")

# building ChromeDB
def build_chromedb_index(df,texts, embeddings, config):
    persist_dir = config["vector_store"]["persist_directory"]
    collection_name = config["vector_store"]["collection_name_chroma"]
    logical_batch_size = config["vector_store"].get("chroma_batch_size", 100000)
    chroma_max_batch = 5461  # ChromaDB's max batch size

    # Get metadata
    metadatas = load_metadata_from_pickle(config["vector_store"]["metadata_path"])

    print("🧠 Logical batch size:", logical_batch_size)

    # Create directory if it doesn't exist
    os.makedirs(persist_dir, exist_ok=True)

    # Initialize Chroma client with PersistentClient instead
    client = chromadb.PersistentClient(path=persist_dir)

    # Create or get collection
    collection = client.get_or_create_collection(name=collection_name)

    # Create IDs
    ids = [f"id_{i}" for i in range(len(texts))]

    # Step through logical batch size
    for i in range(0, len(texts), logical_batch_size):
        batch_texts = texts[i:i + logical_batch_size]
        batch_embeddings = embeddings[i:i + logical_batch_size]
        batch_ids = ids[i:i + logical_batch_size]
        batch_metadata = metadatas[i:i + logical_batch_size]

        # Sub-batch to fit ChromaDB's max limit
        for j in range(0, len(batch_texts), chroma_max_batch):
            sub_texts = batch_texts[j:j + chroma_max_batch]
            sub_embeds = batch_embeddings[j:j + chroma_max_batch]
            sub_ids = batch_ids[j:j + chroma_max_batch]
            sub_meta = batch_metadata[j:j + chroma_max_batch]

            collection.add(
                documents=sub_texts,
                embeddings=sub_embeds.tolist(),
                ids=sub_ids,
                metadatas=sub_meta
            )

        print(f"✅ Uploaded logical batch {i}-{i + len(batch_texts)}")

    print(f"✅ Stored {len(texts)} items in ChromaDB at '{persist_dir}'")

    # Verify collection count
    count = collection.count()
    print(f"✅ Collection contains {count} documents")

# building pinecone
def build_pinecone_index(df,texts, embeddings, config):
    # Get secrets from environment
    api_key = config_db.get("PINECONE_API_KEY")
    environment = config_db.get("PINECONE_ENVIRONMENT")

    # Config values
    index_name = config["vector_store"]["index_name"]
    dimension = config["vector_store"]["dimension"]
    namespace = config["vector_store"]["namespace"]
    metric = config["vector_store"]["metric"]
    batch_size = config["vector_store"]["batch_size"]

    if not api_key:
        raise ValueError("Missing PINECONE_API_KEY .env")

    # Initialize Pinecone client
    pc = Pinecone(api_key=api_key)

    # Create index if it doesn't exist
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(
                cloud="aws",
                region=environment
            )
        )
        print(f"✅ Created Pinecone index: {index_name}")

    # Connect to the index
    index = pc.Index(index_name)

    # Prepare and upload vectors
    vectors = [
        (f"id-{i}", embedding.tolist(), {"text": text})
        for i, (text, embedding) in enumerate(zip(texts, embeddings))
    ]

    for i in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[i:i + batch_size], namespace=namespace)

    print(f"Uploaded {len(vectors)} vectors to Pinecone index '{index_name}' in namespace '{namespace}'")


# core controller
def build_vector_store(config_path):
    config = read_param(config_path)

    df = pd.read_csv(config["data"]["loc"])
    texts = df["sql_prompt"].tolist()

    model_name = config["embedding_model"]
    embeddings = get_embeddings(texts, model_name)

    store_type = config["vector_store"]["type"].lower()

    if store_type == "faiss":
        build_faiss_index(df,texts, embeddings, config)
    elif store_type == "chromadb":
        build_chromedb_index(df,texts, embeddings, config)
    elif store_type == "pinecone":
        build_pinecone_index(df,texts,embeddings, config)
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="params.yaml")
    parsed_args = parser.parse_args()

    build_vector_store(config_path=parsed_args.config)