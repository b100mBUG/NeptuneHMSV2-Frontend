from kivy.storage.jsonstore import JsonStore
import os, sys, platform

SERVER_URL = "https://neptunev2.onrender.com/"


def get_app_data_path(filename):
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif system == "Darwin": 
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:  
        base = os.path.join(os.path.expanduser("~"), ".local", "share")

    if not os.path.exists(base):
        os.makedirs(base, exist_ok=True)

    return os.path.join(base, filename)


json_path = get_app_data_path("hospital_data.json")


STORE = JsonStore(json_path)


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)