"""
yt-cli - Módulo de Configuración y Constantes
"""

import sys
import time
import subprocess
import threading
import itertools
import logging

class Config:
    LOG_FILE: str = "/tmp/yt-cli.log"
    RESET: str   = "\033[0m"
    BOLD: str    = "\033[1m"
    CYAN: str    = "\033[96m"
    GREEN: str   = "\033[92m"
    YELLOW: str  = "\033[93m"
    MAGENTA: str = "\033[95m"
    DIM: str     = "\033[2m"

class LoggerSetup:
    @staticmethod
    def init() -> None:
        logging.basicConfig(
            filename=Config.LOG_FILE,
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - [%(module)s] %(message)s"
        )

class Utils:
    @staticmethod
    def format_time(duration: any) -> str:
        if isinstance(duration, (int, float)):
            m, s = divmod(int(duration), 60)
            h, m = divmod(m, 60)
            return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"
        return str(duration) if duration else "0:00"

    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        clipboard_cmds = [["xclip", "-selection", "clipboard"], ["wl-copy"]]
        for cmd in clipboard_cmds:
            try:
                with subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True) as p:
                    p.communicate(input=text)
                    if p.returncode == 0: 
                        return True
            except FileNotFoundError:
                continue
        return False

class Spinner:
    def __init__(self, message: str = "Cargando..."):
        self.spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.message = message
        self.stop_running = threading.Event()
        self.thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        while not self.stop_running.is_set():
            sys.stdout.write(f"\r{Config.CYAN}{next(self.spinner)} {Config.BOLD}{self.message}{Config.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()

    def start(self): 
        self.thread.start()
        
    def stop(self):
        self.stop_running.set()
        self.thread.join()