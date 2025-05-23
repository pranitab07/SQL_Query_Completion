import pyperclip
import keyboard
import pyautogui
import time
import pygetwindow as gw
import yaml
import argparse
from llm import query_groq_llama
from retrieve_context import get_similar_context
import datetime
import os
import csv

ghost_displayed = False
ghost_text = ""
last_suggestion = ""
session_memory = []

def log_suggestion(user_input, retrieved_context, suggestion, status, latency_ms,vector_store,embedding_model):
    os.makedirs("logs", exist_ok=True)
    log_path = "logs/suggestions_log.csv"
    file_exists = os.path.isfile(log_path)

    with open(log_path, "a", encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)

        # Write headers if file doesn't exist
        if not file_exists:
            writer.writerow([
                "timestamp",
                "model",
                "status",
                "user_input",
                "retrieved_context",
                "llm_suggestion",
                "latency_ms",
                "vector_store",
                "embedding_model"
            ])

        writer.writerow([
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            config['llm']['model_name'],
            status,
            user_input.replace('\n', '\\n'),
            retrieved_context.replace('\n', '\\n'),
            suggestion.replace('\n', '\\n'),
            latency_ms,
            vector_store,
            embedding_model
        ])
        
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
    Takes in metadata rows and builds a richer LLM context string,
    including similarity scores.
    """
    context_blocks = []
    for row in rows:
        block = f"""Prompt: {row['sql_prompt']}
            SQL: {row.get('sql', 'N/A')}
            Explanation: {row.get('sql_explanation', 'N/A')}
            Similarity Score: {row.get('similarity_score', 'N/A'):.4f}"""
        context_blocks.append(block)
    return "\n\n".join(context_blocks)

def get_real_suggestion(user_input, config):
    try:
        # Retrieve similar context rows and format them
        similar_rows = get_similar_context(user_input, config_path="params.yaml", top_k=config["vector_store"]["top_k"])
        context = format_context(similar_rows)

        # Optional: Include session memory if enabled
        full_context = context
        if config.get("memory", {}).get("enable", False):
            limit = config["memory"].get("limit", 3)
            session_context = "\n\n".join(session_memory[-limit:])
            if session_context:
                full_context = f"{session_context}\n\n{context}"

        response = query_groq_llama(user_input=user_input, context=full_context, config=config)

        if config.get("memory", {}).get("enable", False):
            session_memory.append(f"Prompt: {user_input}\nResponse: {response}")
        
        return response, context
    except Exception as e:
        print(f"[ERROR] Failed to get suggestion: {e}")
        return "(error generating suggestion)", ""

def handle_ctrl_c():
    global ghost_displayed, ghost_text, config, last_suggestion, copied_text, context, latency_ms

    # Waiting text to get added in clipboard
    time.sleep(config["base"]["sleep_time"])
    copied_text = pyperclip.paste().strip()

    # Getting the current active window
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

    # Get suggestion and context from LLM
    start_time = time.time()
    suggestion, context = get_real_suggestion(user_input, config)
    end_time = time.time()
    latency_ms = (end_time - start_time)
    last_suggestion = suggestion

    # Show ghost suggestion as a comment
    ghost_text = f"/* suggestion: {suggestion} */"
    pyautogui.press('right')
    pyautogui.press('enter')
    pyautogui.write(ghost_text, interval=config["triggers"]["speed_write"])
    ghost_displayed = True

def handle_tab():
    global ghost_displayed, ghost_text, last_suggestion, copied_text, context, config

    if ghost_displayed:
        # Remove ghost suggestion
        pyautogui.hotkey('ctrl', 'z')
        pyautogui.hotkey('ctrl', 'z')
        pyautogui.press('enter')

        # Insert actual suggestion
        pyautogui.write(last_suggestion, interval = config["triggers"]["speed_write"])

        # Log the accepted suggestion
        log_suggestion(
            user_input = copied_text,
            retrieved_context = context,
            suggestion = last_suggestion,
            status = "ACCEPTED",
            latency_ms = latency_ms,
            vector_store = config["vector_store"]["type"],
            embedding_model = config["embedding_model"]
        )

        ghost_displayed = False

def handle_any_other_key(e):
    global ghost_displayed, copied_text, context, last_suggestion, config

    if ghost_displayed:
        print("🚫 Suggestion dismissed.")

        # Remove ghost suggestion
        pyautogui.hotkey('ctrl','z')
        pyautogui.hotkey('ctrl','z')

        # Log as dismissed
        log_suggestion(
            user_input=copied_text,
            retrieved_context=context,
            suggestion=last_suggestion,
            status="DISMISSED",
            latency_ms = latency_ms,
            vector_store = config["vector_store"]["type"],
            embedding_model = config["embedding_model"]
        )

        ghost_displayed = False

def main(config_path):
    print("👀 Listening for Ctrl+C and Tab... (press Esc to quit)")
    global config

    config = read_param(config_path)

    # We don’t need to load FAISS or metadata here — handled in retrieve_context
    keyboard.add_hotkey(config["triggers"]["initiater"], handle_ctrl_c)
    keyboard.add_hotkey(config["triggers"]["filler"], handle_tab)

    # Add memory reset hotkey
    keyboard.add_hotkey("ctrl+shift+c", lambda: (session_memory.clear(), print("🧹 Session memory cleared")))

    for key in [chr(i) for i in range(32, 127)]:
        if key != config["triggers"]["key"]:
            keyboard.on_press_key(key, handle_any_other_key, suppress=False)

    keyboard.wait(config["triggers"]["quiting"])

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", default="params.yaml")
    parsed_args = args.parse_args()
    main(config_path=parsed_args.config)