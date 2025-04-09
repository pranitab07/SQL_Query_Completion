import pyperclip
import keyboard
import pyautogui
import time
import pygetwindow as gw
import yaml
import argparse
from src.llm import query_groq_llama
from src.retrieve_context import get_similar_context
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import numpy as np
import re
import datetime
import os

ghost_displayed = False
ghost_text = ""
last_suggestion = ""

def log_suggestion(user_input, retrieved_context, suggestion):
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/suggestions_log.txt"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n" + "="*60 + "\n")
        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        f.write(f"USER INPUT:\n{user_input}\n\n")
        f.write(f"RETRIEVED CONTEXT:\n{retrieved_context}\n\n")
        f.write(f"LLM SUGGESTION:\n{suggestion}\n")
        
def read_param(config_path):
    with open(config_path) as yaml_file:
        return yaml.safe_load(yaml_file)

def get_active_window_title():
    try:
        return gw.getActiveWindowTitle()
    except:
        return ""

def format_context(rows):
    """
    Takes in metadata rows and builds a richer LLM context string.
    """
    context_blocks = []
    for row in rows:
        block = f"""Prompt: {row['sql_prompt']}
SQL: {row.get('sql', 'N/A')}
Explanation: {row.get('sql_explanation', 'N/A')}"""
        context_blocks.append(block)
    return "\n\n".join(context_blocks)

def get_real_suggestion(user_input, config):
    try:
        similar_rows = get_similar_context(user_input, config_path="params.yaml", top_k=config["vector_store"]["top_k"])
        context = format_context(similar_rows)
        response = query_groq_llama(user_input=user_input, context=context)

        # ✅ Log the interaction
        log_suggestion(user_input, context, response)

        return response
    except Exception as e:
        print(f"[ERROR] Failed to get suggestion: {e}")
        return "-- suggestion: (error generating suggestion)"

def handle_ctrl_c():
    global ghost_displayed, ghost_text, config, last_suggestion

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

    # Clean comments for embedding input
    user_input = copied_text.strip()
    if not user_input:
        print("⚠️ Clipboard is empty.")
        return

    suggestion = get_real_suggestion(user_input, config)
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
    global config

    config = read_param(config_path)

    # We don’t need to load FAISS or metadata here — handled in retrieve_context
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