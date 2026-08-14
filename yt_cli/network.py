"""
yt-cli - Módulo de Red y Extracción (yt-dlp)
"""

import subprocess
import json
import sys
import os
import logging
from typing import List, Dict, Iterator

from yt_cli.config import Config, Spinner, Utils

class YouTubeNetwork:
    @staticmethod
    def search(query: str, limit: int = 40) -> List[Dict[str, str]]:
        logging.info(f"Iniciando búsqueda para: {query}")
        os.system('clear')
        loader = Spinner(f"Buscando '{query}' en YouTube...")
        loader.start()
        
        cmd = [
            "yt-dlp", f"ytsearch{limit}:{query}", 
            "--print-json", "--flat-playlist", 
            "--quiet", "--no-warnings", "--ignore-errors"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except Exception as e:
            loader.stop()
            logging.critical(f"Error de red: {e}")
            print(f"\n{Config.YELLOW}Error al conectar. Revisa {Config.LOG_FILE}.{Config.RESET}")
            sys.exit(1)
        finally:
            loader.stop()

        def _parse_lines(lines: List[str]) -> Iterator[Dict[str, str]]:
            for line in lines:
                if not line.strip(): 
                    continue
                try:
                    data = json.loads(line)
                    raw_duration = data.get("duration_string") or data.get("duration")
                    yield {
                        "title": data.get("title", "Desconocido"), 
                        "uploader": data.get("uploader", data.get("channel", "Desconocido")),
                        "duration": Utils.format_time(raw_duration),
                        "url": data.get("url", data.get("webpage_url", ""))
                    }
                except json.JSONDecodeError: 
                    continue

        return list(_parse_lines(result.stdout.splitlines()))