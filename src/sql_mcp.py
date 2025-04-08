import pyperclip
import keyboard
import pyautogui
import time
import pygetwindow as gw
import yaml
import argparse
from src.llm import query_groq_llama
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import numpy as np
import re

ghost_displayed = False
ghost_text = ""
last_suggestion = ""

def read_param(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
        return config

def get_active_window_title():
    try:
        return gw.getActiveWindowTitle()
    except:
        return ""

def get_real_suggestion(user_input, index, metadata, model, config):
    embedding = model.encode([user_input])
    top_k = config["vector_store"]["top_k"]
    _, indices = index.search(np.array(embedding).astype("float32"), top_k)
    context = "\n".join([metadata[i]["sql_prompt"] for i in indices[0]])
    response = query_groq_llama(user_input=user_input, context=context)
    return response

def handle_ctrl_c():
    global ghost_displayed, ghost_text, index, metadata, model, config, last_suggestion

    time.sleep(config["base"]["sleep_time"])
    copied_text = pyperclip.paste().strip()

    active_window = get_active_window_title()
    print(active_window)
    valid_windows = [name.lower() for name in config["base"]["window_name"]]
    if not active_window or not any(valid in active_window.lower() for valid in valid_windows):
        print("🛑 SQL Workbench not active.")
        return

    print("✅ SQL Captured:")
    print(copied_text)

    suggestion = get_real_suggestion(copied_text, index, metadata, model, config)
    last_suggestion = suggestion
    ghost_text = f"  -- suggestion: {suggestion}"
    pyautogui.write(ghost_text, interval=config["triggers"]["speed_write"])
    ghost_displayed = True

def handle_tab():
    global ghost_displayed, ghost_text, last_suggestion, config
    if ghost_displayed:
        pyautogui.hotkey(config["triggers"]["remove_ghost"]["c"], config["triggers"]["remove_ghost"]["key"])
        time.sleep(config["base"]["sleep_time"])
        pyautogui.write(last_suggestion, interval=config["triggers"]["speed_write"])
        ghost_displayed = False

def handle_any_other_key(e):
    global ghost_displayed, config
    if ghost_displayed:
        print("🚫 Suggestion dismissed.")
        pyautogui.hotkey(config["triggers"]["remove_ghost"]["c"], config["triggers"]["remove_ghost"]["key"])
        ghost_displayed = False

def main(config_path):
    print("👀 Listening for Ctrl+C and Tab... (press Esc to quit)")
    global config, index, metadata, model

    config = read_param(config_path)

    print("📦 Loading FAISS index and metadata...")
    index = faiss.read_index(config["vector_store"]["index_path"])
    with open(config["vector_store"]["metadata_path"], "rb") as f:
        metadata = pickle.load(f)

    model = SentenceTransformer("all-MiniLM-L6-v2")

    keyboard.add_hotkey(config["triggers"]["initiater"], handle_ctrl_c)
    keyboard.add_hotkey(config["triggers"]["filler"], handle_tab)

    for key in [chr(i) for i in range(32, 127)]:
        if key != config["triggers"]["key"]:
            keyboard.on_press_key(key, handle_any_other_key, suppress=False)

    keyboard.wait(config["triggers"]["quiting"])

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", default="params.yaml")
    parsed_args = args.parse_args()
    main(config_path=parsed_args.config)
