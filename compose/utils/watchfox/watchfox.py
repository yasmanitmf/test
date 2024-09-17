import difflib
import json
import time
from pathlib import Path
from typing import Callable, Dict, Any, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_PATH = Path(__file__).parent / 'config.json'

class FileChangeHandler(FileSystemEventHandler):
    """
    Handles file modification events.
    """
    def __init__(self, config: str|Path|Dict[str, Any]=CONFIG_PATH, callback: Optional[Callable[[Dict[Path, Dict[str, Any]]], None]] = None):
        """
        Initializes the FileChangeHandler.

        Args:
            config: Configuration dictionary.
            callback: Optional callback function to execute on file modification.
        """
        if isinstance(config, (str,Path)):
            with open(config, 'r') as config_file:
                config = json.load(config_file)
        
        self.basedir = Path(config['basedir'])
        self.files_to_watch = {
            str(self.basedir / file): {'timestamp': 0, 'content': self.read_file(self.basedir / file), 'diff': []} for file in config['files']
        }
        self.debounce_interval = config.get('debounce_interval', 1)
        self.min_line_diff = config.get('min_line_diff', 1)
        self.file_status = config.get('state_file', CONFIG_PATH.parent/'report.json')
        self.callback = callback

    def read_file(self, file_path: Path|str) -> List[str]:
        """
        Reads the content of a file.

        Args:
            file_path: Path to the file.

        Returns:
            List of lines in the file.
        """
        try:
            with open(file_path, 'r') as file:
                return file.readlines()
        except IOError:
            return []

    def status_to_disk(self) -> None:
        """
        Writes the current state of files_to_watch to a JSON file.
        """
        with open(self.file_status, 'w') as f:
            json.dump(self.files_to_watch, f, indent=4)

    def validate_timestamp(self, file_path: Path|str) -> bool:
        """
        Validates the timestamp to check if debounce interval has passed.

        Args:
            file_path: Path to the file.

        Returns:
            True if the debounce interval has passed, otherwise False.
        """
        current_time = time.time()
        time_diff = current_time - self.files_to_watch[file_path]['timestamp'] > self.debounce_interval
        if time_diff:
            self.files_to_watch[file_path]['timestamp'] = current_time
        return time_diff 

    def validate_length_diff(self, file_path: Path|str) -> bool:
        """
        Validates the length difference of the file content.

        Args:
            file_path: Path to the file.

        Returns:
            True if the number of lines in diff is greater than min_line_diff, otherwise False.
        """
        new_content = self.read_file(file_path)
        diff = [line for line in difflib.unified_diff(self.files_to_watch[file_path]['content'], new_content)]
        length_diff = sum(1 for line in diff if line.startswith(('---', '+++', '@@'))) > self.min_line_diff
        
        if length_diff:
            self.files_to_watch[file_path]['content'] = new_content
            self.files_to_watch[file_path]['diff'] = diff
        return length_diff

    def on_modified(self, event) -> None:
        """
        Handles the file modification event.

        Args:
            event: File system event.
        """
        if (file_path:=event.src_path) in self.files_to_watch:
            timestamp_alert = self.validate_timestamp(file_path)
            length_diff_alert = self.validate_length_diff(file_path)
            
            if timestamp_alert and length_diff_alert:
                if self.callback:
                    self.callback({file_path: self.files_to_watch[file_path]})


class WatchFox:
    """
    Encapsulates the Observer and FileChangeHandler.
    """
    def __init__(self, config: str|Dict[str, Any]=CONFIG_PATH, on_modified: Optional[Callable[[Dict[Path|str, Dict[str, Any]]], None]] = None):
        """
        Initializes the WatchFox.

        Args:
            config: Configuration dictionary.
            on_modified: Optional callback function to execute on file modification.
        """
        self.config = config
        self.event_handler = FileChangeHandler(config, callback=on_modified)
        self.observer = Observer()

    def start(self) -> None:
        """
        Starts the observer.
        """
        self.observer.schedule(self.event_handler, path=self.event_handler.basedir, recursive=True)
        self.observer.start()

    def stop(self) -> None:
        """
        Stops the observer.
        """
        self.observer.stop()
        self.observer.join()


if __name__ == "__main__":
    watchfox = WatchFox()
    watchfox.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watchfox.stop()

