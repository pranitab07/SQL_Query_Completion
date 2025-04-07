import pandas as pd
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import os
import argparse
import yaml

def read_param(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
        return config

def build_faiss_index(config_path):
    config = read_param(config_path)
    
    df = pd.read_csv(config["data"]["loc"])
    texts = df["sql_prompt"].tolist()

    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, show_progress_bar=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    index_path = config["vector_store"]["index_path"]
    metadata_path = config["vector_store"]["metadata_path"]

    os.makedirs(os.path.dirname(index_path), exist_ok=True)

    faiss.write_index(index, index_path)
    with open(metadata_path, "wb") as f:
        pickle.dump(df.to_dict("records"), f)

    print("FAISS vector store and metadata saved.")

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", default="params.yaml")
    parsed_args = args.parse_args()

    build_faiss_index(config_path=parsed_args.config)