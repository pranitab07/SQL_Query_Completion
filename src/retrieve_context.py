import faiss
import pickle
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
import yaml

def read_param(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
        return config

def get_similar_context(query, config_path="params.yaml", top_k=5):
    config = read_param(config_path)

    # Load FAISS index and metadata
    index = faiss.read_index(config["vector_store"]["index_path"])
    with open(config["vector_store"]["metadata_path"], "rb") as f:
        metadata = pickle.load(f)

    # Load embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_vector = model.encode([query])

    # Search top_k results
    distances, indices = index.search(np.array(query_vector), top_k)
    results = [metadata[i] for i in indices[0]]

    return results