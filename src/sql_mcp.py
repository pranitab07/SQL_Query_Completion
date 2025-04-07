import pyperclip
import keyboard
import pyautogui
import time
import pygetwindow as gw
import yaml
import argparse

# Fake suggestion for testing Purpose
fake_suggestion = "SELECT * FROM customers WHERE city = 'Berlin';"
ghost_displayed = False
ghost_text = f"  -- suggestion: {fake_suggestion}"

def read_param(config_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
        return config

def get_active_window_title():
    try:
        return gw.getActiveWindowTitle()
    except:
        return ""

def handle_ctrl_c():
    global ghost_displayed
    time.sleep(config["base"]["sleep_time"])
    copied_text = pyperclip.paste()

    active_window = get_active_window_title()
    print(active_window)
    valid_windows = [name.lower() for name in config["base"]["window_name"]]
    if not active_window or not any(valid in active_window.lower() for valid in valid_windows):
        print("🛑 SQL Workbench not active.")
        return

    print("✅ SQL Captured:")
    print(copied_text)
    time.sleep(config["base"]["sleep_time"])

    # Show ghost suggestion as comment
    pyautogui.write(ghost_text, interval=config["triggers"]["speed_write"])
    ghost_displayed = True

def handle_tab():
    global ghost_displayed
    if ghost_displayed:

        # removing ghost letters
        pyautogui.hotkey(config["triggers"]["remove_ghost"]["c"],config["triggers"]["remove_ghost"]["key"]) 
        time.sleep(config["base"]["sleep_time"])
        pyautogui.write(fake_suggestion, interval=config["triggers"]["speed_write"])
        ghost_displayed = False

def handle_any_other_key(e):
    global ghost_displayed
    if ghost_displayed:

        print("🚫 Suggestion dismissed.")

        # removing ghost letters
        pyautogui.hotkey(config["triggers"]["remove_ghost"]["c"],config["triggers"]["remove_ghost"]["key"]) 
        ghost_displayed = False

def main(config_path):
    print("👀 Listening for Ctrl+C and Tab... (press Esc to quit)")
    # Getting the config path of yaml file
    global config
    config = read_param(config_path)

    keyboard.add_hotkey(config["triggers"]["initiater"], handle_ctrl_c)
    keyboard.add_hotkey(config["triggers"]["filler"], handle_tab)

    # Listen for all keys; if ghost is shown, dismiss on any non-tab key
    for key in [chr(i) for i in range(32, 127)]:
        if key != config["triggers"]["key"]:
            keyboard.on_press_key(key, handle_any_other_key, suppress=False)

    keyboard.wait(config["triggers"]["quiting"])

if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config",default="params.yaml")
    parsed_args = args.parse_args()
    main(config_path=parsed_args.config)