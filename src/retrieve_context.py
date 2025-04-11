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

def get_similar_context(query, config_path="params.yaml", top_k=None):
    config = read_param(config_path)
    if top_k is None:
        top_k = config["vector_store"]["top_k"]
    
    # Load FAISS index and metadata
    index = faiss.read_index(config["vector_store"]["index_path"])
    with open(config["vector_store"]["metadata_path"], "rb") as f:
        metadata = pickle.load(f)

    # Load embedding model
    model = SentenceTransformer(config["embedding_model"])
    query_vector = model.encode([query])

    # Search top_k results
    distances, indices = index.search(np.array(query_vector), top_k)
    results = [
    {**metadata[i], "similarity_score": float(distances[0][idx])}
    for idx, i in enumerate(indices[0])
]

    return results