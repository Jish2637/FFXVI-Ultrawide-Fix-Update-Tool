import os
import sys
import requests
import zipfile
import shutil
import json
from tkinter import Tk, filedialog, messagebox

config_file = "config.json"
version_file = "version.txt"

def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

def save_config(config):
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=4)

def load_local_version():
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            return f.read().strip()
    return None

def save_local_version(version):
    with open(version_file, 'w') as f:
        f.write(version)

def ask_for_game_folder():
    messagebox.showinfo("Select Game Folder", "Please select your game folder.")
    root = Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory()
    if not folder_selected:
        messagebox.showerror("Error", "No folder selected, exiting.")
        exit_application()
    return folder_selected

def show_message(title, message):
    root = Tk()
    root.withdraw()
    messagebox.showinfo(title, message)

def show_error(title, message):
    root = Tk()
    root.withdraw()
    messagebox.showerror(title, message)

def exit_application():
    sys.exit(0)

def detect_game_folder():
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.realpath(__file__))
    
    if os.path.exists(os.path.join(current_dir, "ffxvi.exe")):
        return current_dir
    return None

game_folder = detect_game_folder()

if game_folder:
    answer = messagebox.askyesno("Game Detected", f"FFXVI has been detected in {game_folder}. Do you want to update?")
    if not answer:
        show_message("Aborted", "Update process aborted by user.")
        exit_application()
else:
    config = load_config()

    if not config:
        config = {}
        config["repo"] = "Lyall/FFXVIFix"
        config["game_folder"] = ask_for_game_folder()
        save_config(config)

    game_folder = config["game_folder"]

repo = "Lyall/FFXVIFix"
download_folder = os.path.join(game_folder, "FFXVIFix_Latest")
latest_release_url = f"https://api.github.com/repos/{repo}/releases/latest"

if not os.path.exists(download_folder):
    os.makedirs(download_folder)

try:
    response = requests.get(latest_release_url, headers={"Accept": "application/vnd.github.v3+json"})
    response.raise_for_status()
    release_data = response.json()
    latest_version = release_data["tag_name"]
except requests.exceptions.RequestException as e:
    show_error("Error", f"Failed to fetch release data: {e}")
    exit_application()

local_version = load_local_version()

if local_version == latest_version:
    answer = messagebox.askyesno("Up to Date", f"You are already up to date (version {latest_version}). Do you want to re-download anyway?")
    if not answer:
        show_message("Up to Date", "You are up to date. No changes were made.")
        exit_application()
else:
    answer = messagebox.askyesno("Update Available", f"A new version {latest_version} is available. Do you want to update?")
    if not answer:
        show_message("No Update", "You chose not to update.")
        exit_application()

download_url = release_data["assets"][0]["browser_download_url"]

show_message("Downloading", f"Downloading latest release from {download_url}")
latest_release_zip = os.path.join(download_folder, "latest_release.zip")

try:
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(latest_release_zip, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
except requests.exceptions.RequestException as e:
    show_error("Download Failed", f"Failed to download file: {e}")
    exit_application()

if not os.path.exists(latest_release_zip):
    show_error("Error", "Download failed or file not found!")
    exit_application()

with zipfile.ZipFile(latest_release_zip, 'r') as zip_ref:
    zip_ref.extractall(game_folder)

os.remove(latest_release_zip)
if os.path.exists(os.path.join(game_folder, "EXTRACT_TO_GAME_FOLDER")):
    os.remove(os.path.join(game_folder, "EXTRACT_TO_GAME_FOLDER"))
if os.path.exists(download_folder):
    shutil.rmtree(download_folder)

save_local_version(latest_version)

show_message("Update Complete", f"The latest release (version {latest_version}) has been downloaded and applied successfully!")
