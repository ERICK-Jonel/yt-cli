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
        
        mode_text = "SÓLO AUDIO" if audio_only else "VIDEO & AUDIO"
        badge_color = Config.MAGENTA if audio_only else Config.CYAN
        
        # Interfaz con estilo coherente a la lista de resultados (bordes y colores limpios)
        print(f"\n{badge_color}{Config.BOLD}┌──────────────────────────────────────────────────────────────────────┐{Config.RESET}")
        print(f"{badge_color}{Config.BOLD}│{Config.RESET} {Config.BOLD} REPRODUCIENDO [{mode_text}]{Config.RESET}")
        print(f"{badge_color}{Config.BOLD}└──────────────────────────────────────────────────────────────────────┘{Config.RESET}")
        print(f" {Config.GREEN}{video_data['duration']:>7}{Config.RESET} {Config.DIM}│{Config.RESET} {Config.YELLOW}{video_data['uploader'][:30]:<30}{Config.RESET}")
        print(f" {Config.DIM}└─ Título :{Config.RESET} {video_data['title']}")
        print(f" {Config.DIM}└─ Enlace :{Config.RESET} {video_data['url']}\n")
        print(f"{Config.DIM}──────────────────────────────────────────────────────────────────────{Config.RESET}\n")
        
        # Comando para mpv (mantiene la salida nativa de pistas y tags que te gusta)
        cmd = ["mpv", video_data['url'], "--ytdl-raw-options=cookies-from-browser=firefox"]
        if audio_only: 
            cmd.append("--no-video")
            
        subprocess.run(cmd)