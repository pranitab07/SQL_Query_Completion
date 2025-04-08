# src/query_with_rag.py
import os
import pickle
import faiss
import yaml
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from src.llm import query_groq_llama  # import from previous step

# Load env variables
load_dotenv()

def read_param(config_path):
    with open(config_path) as yaml_file:
        return yaml.safe_load(yaml_file)

def retrieve_relevant_prompts(user_question, config_path="params.yaml", top_k=3):
    # Load config
    config = read_param(config_path)

    # Load metadata
    with open(config["vector_store"]["metadata_path"], "rb") as f:
        metadata = pickle.load(f)

    # Load FAISS index
    index = faiss.read_index(config["vector_store"]["index_path"])

    # Load embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Embed user question
    question_embedding = model.encode([user_question])

    # Search FAISS
    _, indices = index.search(question_embedding, top_k)

    # Retrieve top prompts
    relevant_prompts = [metadata[i]["sql_prompt"] for i in indices[0]]
    return relevant_prompts