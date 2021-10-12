import json
import atexit
import os


class JSONStorage:
    """Stores data as a JSON file"""

    def __init__(self, path):
        self.data = {}
        self.path = os.path.join("data", path)
        self.load_json()

    def load_json(self):
        """Loads JSON from path"""
        try:
            with open(self.path) as file:
                self.data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.path, "w") as file:
                json.dump({}, file)

    @atexit.register
    def save_json(self):
        """Save JSON to path"""
        with open(self.path, "w") as file:
            json.dump(self.data, file)