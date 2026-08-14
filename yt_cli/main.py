#!/usr/init/env python3
"""
yt-cli - Orquestador Principal
"""

import sys
import os
from typing import List, Tuple, Dict

from yt_cli.config import Config, LoggerSetup, Utils
from yt_cli.network import YouTubeNetwork
from yt_cli.player import Player
from yt_cli.ui import UI

def main() -> int:
    LoggerSetup.init()
    if len(sys.argv) < 2:
        query = input(f"{Config.YELLOW}¿Qué deseas buscar?: {Config.RESET}")
    else:
        query = " ".join(sys.argv[1:])

    while True:
        videos = YouTubeNetwork.search(query)
        if not videos: 
            break
        
        while True:
            key, selected_line = UI.prompt_fzf(videos)
            
            if not key and not selected_line: 
                sys.exit(0)
            if key == "ctrl-h": 
                UI.show_help()
            elif key == "ctrl-n": 
                new_query = input(f"{Config.YELLOW}¿Qué deseas buscar ahora? (Dejar vacío para cancelar): {Config.RESET}").strip()
                if new_query:
                    query = new_query
                    break
            elif selected_line:
                idx = int(selected_line.split("||")[0])
                chosen = videos[idx]
                if key == "ctrl-y": 
                    Utils.copy_to_clipboard(chosen['url'])
                else: 
                    Player.play(chosen, audio_only=(key == "ctrl-a"))
    return 0

if __name__ == "__main__":
    sys.exit(main())