import subprocess
import json
from pathlib import Path
import time
from typing import Dict, Any
from colorama import init, Fore, Style
from watchfox import WatchFox, CONFIG_PATH

init(autoreset=True)

def on_modified(state: Dict[Path|str, Dict[str, Any]]) -> None:
    """
    External API callback to be triggered on file modification.

    Args:
        state: The current state of file being watched.
    """
    with open(CONFIG_PATH, 'r') as config_file:
        config = json.load(config_file)
    (file_path, _), = state.items()
    
    try:
        PASSWORD_POLICIES_SCRIPT = Path(CONFIG_PATH).parent / 'password_policies.py'
        report = subprocess.run([
            'python3', PASSWORD_POLICIES_SCRIPT,
            '-c', CONFIG_PATH,
            '-i', str(file_path),
            '-m', str(Path(file_path).relative_to(config['basedir']).with_suffix('')).replace('/', '.'),
            # '-d'
        ], capture_output=True, text=True)
        
        if report.returncode == 0:
            try:
                policy_tests = json.loads(report.stdout)
                if not all(policy_tests.values()):
                    message = config['warning_message']
                    border = "-" * (len(message) + 15)
                    formatted_message = (
                        f"{Fore.RED}{Style.BRIGHT}{border}\n"
                        f"{Fore.RED}{Style.BRIGHT}| Warning: {message}{Fore.RED}{Style.BRIGHT} \n"
                        f"{Fore.RED}{Style.BRIGHT}{border}\n"
                    )
                    escaped_message = formatted_message.replace('"', '\\"').replace('$', '\\$')
                    subprocess.run(['echo', '-e', escaped_message], shell=False)
            except json.JSONDecodeError as json_error:
                pass
        else:
            pass
    except Exception as e:
        pass
    

if __name__ == "__main__":
    watchfox = WatchFox(on_modified=on_modified)
    watchfox.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watchfox.stop()
