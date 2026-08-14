"""
yt-cli - Módulo Reproductor Multimedia (mpv)
"""

import subprocess
import os
from typing import Dict

from yt_cli.config import Config

class Player:
    @staticmethod
    def play(video_data: Dict[str, str], audio_only: bool = False) -> None:
        os.system('clear')
        mode_text = "♫ SÓLO AUDIO" if audio_only else "🎬 VIDEO"
        color = Config.MAGENTA if audio_only else Config.CYAN
        
        print(f"\n{color}{Config.BOLD}======================================================================{Config.RESET}")
        print(f"{color}{Config.BOLD} ♫ REPRODUCIENDO ({mode_text}){Config.RESET}")
        print(f"{color}{Config.BOLD}======================================================================{Config.RESET}")
        print(f" {Config.CYAN}♪ Título  :{Config.RESET} {video_data['title']}")
        print(f" {Config.YELLOW}👤 Canal   :{Config.RESET} {video_data['uploader']}")
        print(f" {Config.DIM}⏱ Duración:{Config.RESET} {video_data['duration']}\n")
        
        cmd = ["mpv", video_data['url'], "--ytdl-raw-options=cookies-from-browser=firefox"]
        if audio_only: 
            cmd.append("--no-video")
            
        subprocess.run(cmd)