import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

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
import csv
import time
from db_schema_utils import read_db_config, create_connection, extract_schema_with_examples

# Set working directory to where the executable was bundled
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable))

ghost_displayed = False
ghost_text = ""
last_suggestion = ""
session_memory = []

def log_suggestion(user_input, retrieved_context, suggestion, status, latency_ms, db_schema):
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
                "db_name",
                "db_schema",        
                "llm_suggestion",
                "latency_ms"
            ])

        db_name     = config["db"]["name"]
        schema_snip = db_schema.replace('\n', '\\n')[:200]
        writer.writerow([
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            config['llm']['model_name'],
            status,
            user_input.replace('\n', '\\n'),
            retrieved_context.replace('\n', '\\n'),
            db_name,           # ← new field
            schema_snip,       # ← new field
            suggestion.replace('\n', '\\n'),
            latency_ms
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
        # Try to load user DB schema
        try:
            db_cfg = read_db_config()
            engine = create_connection(db_cfg)
            db_schema_context = extract_schema_with_examples(
                engine,
                db_cfg["name"],
                sample_rows=db_cfg.get("sample_rows", 2)
            )
            # cache it for later
            get_real_suggestion._cached_schema = db_schema_context
        except Exception as db_err:
            print(f"[WARN] DB schema load failed—using cached or empty. ({db_err})")
            db_schema_context = getattr(get_real_suggestion, "_cached_schema", "")

        # Retrieve similar context rows and format them
        similar_rows = get_similar_context(
            user_input,
            config_path="params.yaml",
            top_k=config["vector_store"]["top_k"]
        )
        rag_context = format_context(similar_rows)

        # Include session memory if enabled
        if config.get("memory", {}).get("enable", False):
            limit = config["memory"].get("limit", 3)
            session_context = "\n\n".join(session_memory[-limit:])
        else:
            session_context = ""
            
        # Build full LLM prompt context
        parts = [db_schema_context, session_context, rag_context]
        full_context = "\n\n".join([p for p in parts if p]).strip()
        
        # Call LLM
        response = query_groq_llama(
            user_input=user_input,
            context=full_context,
            config=config
        )

        # Append to session memory if enabled
        if config.get("memory", {}).get("enable", False):
            session_memory.append(f"Prompt: {user_input}\nResponse: {response}")

        return response, rag_context, db_schema_context
    
    except Exception as e:
        print(f"[ERROR] Failed to get suggestion: {e}")
        return "(error generating suggestion)", "", ""

def handle_ctrl_c():
    global ghost_displayed, ghost_text, config, last_suggestion, copied_text, context, latency_ms, db_schema_context

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
    suggestion, context, db_schema_context = get_real_suggestion(copied_text, config)
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
    global ghost_displayed, ghost_text, last_suggestion, copied_text, context, config, latency_ms, db_schema_context

    if ghost_displayed:
        # Remove ghost suggestion
        pyautogui.hotkey('ctrl', 'z')
        pyautogui.press('enter')

        # Insert actual suggestion
        pyautogui.write(last_suggestion, interval=config["triggers"]["speed_write"])

        # Log the accepted suggestion
        log_suggestion(
            user_input=copied_text,
            retrieved_context=context,
            suggestion=last_suggestion,
            status="ACCEPTED",
            latency_ms=latency_ms,
            db_schema=db_schema_context
        )
        ghost_displayed = False

def handle_any_other_key(e):
    global ghost_displayed, copied_text, context, last_suggestion, config, db_schema_context

    if ghost_displayed:
        print("🚫 Suggestion dismissed.")

        # Remove ghost suggestion
        pyautogui.hotkey(config["triggers"]["remove_ghost"]["c"],
                         config["triggers"]["remove_ghost"]["key"])

        # Log as dismissed
        log_suggestion(
            user_input=copied_text,
            retrieved_context=context,
            suggestion=last_suggestion,
            status="DISMISSED",
            latency_ms=0,
            db_schema=db_schema_context
        )
        ghost_displayed = False

def main(config_path):
    print("👀 Listening for Ctrl+C and Tab... (press Esc to quit)")
    global config

    config = read_param(config_path)
    config["db"] = read_db_config()

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