import pandas as pd
import faiss
import chromadb # type:ignore
from chromadb.config import Settings # type:ignore
import pinecone # type: ignore
from dotenv import load_dotenv
import pickle
from sentence_transformers import SentenceTransformer
import os
import argparse
import yaml

load_dotenv()  # Load environment variables from .env

# defination for reading YAML config
def read_param(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
        return config

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
def build_chromedb_index(texts, embeddings, config):
    persist_dir = config["vector_store"]["persist_directory"]
    collection_name = config["vector_store"]["collection_name_chroma"]

    # Initialize Chroma client
    client = chromadb.Client(Settings(
        persist_directory=persist_dir,
        anonymized_telemetry=False
    ))

    # Create or get collection
    collection = client.get_or_create_collection(name=collection_name)

    # Add texts + embeddings to collection
    ids = [f"id_{i}" for i in range(len(texts))]

    collection.add(
        documents=texts,
        embeddings=embeddings.tolist(),
        ids=ids
    )

    client.persist() 
    print(f"Stored {len(texts)} items in ChromaDB at '{persist_dir}'")

# building pinecone
def build_pinecone_index(texts, embeddings, config):
    # Get secrets from environment
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT")
    
    # Other configs from YAML
    index_name = config["vector_store"]["index_name"]
    dimension = config["vector_store"]["dimension"]
    namespace = config["vector_store"]["namespace"]
    metric = config["vector_store"]["metric"]
    batch_size = config["vector_store"]["batch_size"]

    if not api_key or not environment:
        raise ValueError("Missing PINECONE_API_KEY or PINECONE_ENVIRONMENT in .env")

    # Initialize Pinecone
    pinecone.init(api_key=api_key, environment=environment)

    # Create index if it doesn't exist
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(index_name, dimension=dimension, metric=metric)
        print(f"Created Pinecone index: {index_name}")

    index = pinecone.Index(index_name)

    # Prepare and upload
    vectors = [
        (f"id-{i}", embedding.tolist(), {"text": text})
        for i, (text, embedding) in enumerate(zip(texts, embeddings))
    ]

    # Upload in batches
    for i in range(0, len(vectors), batch_size):
        index.upsert(vectors=vectors[i:i+batch_size], namespace=namespace)

    print(f"Uploaded {len(vectors)} vectors to Pinecone index '{index_name}' in namespace '{namespace}'")


# core controller
def build_vector_store(config_path):
    config = read_param(config_path)

    df = pd.read_csv(config["data"]["loc"])
    texts = df["sql_prompt"].tolist()

    model_name = config["embedding"]["model_name"]
    embeddings = get_embeddings(texts, model_name)

    store_type = config["vector_store"]["type"].lower()

    if store_type == "faiss":
        build_faiss_index(df,texts, embeddings, config)
    elif store_type == "chromedb":
        build_chromedb_index(texts, embeddings, config)
    elif store_type == "pinecone":
        build_pinecone_index(texts,embeddings, config)
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="params.yaml")
    parsed_args = parser.parse_args()

    build_vector_store(config_path=parsed_args.config)