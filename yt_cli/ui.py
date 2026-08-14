"""
yt-cli - Módulo de Interfaces (fzf, menús y ayuda)
"""

import subprocess
import os
import shutil
from typing import List, Tuple

from yt_cli.config import Config

class UI:
    @staticmethod
    def show_help() -> None:
        os.system('clear')
        print(f"{Config.CYAN}{Config.BOLD}=== ♫ yt-cli : Manual de Usuario ==={Config.RESET}\n")
        print(f"{Config.YELLOW}Navegación en la Lista (FZF):{Config.RESET}")
        print(f" {Config.BOLD}[Escribir]{Config.RESET}    : Filtrar resultados en tiempo real")
        print(f" {Config.BOLD}[Enter]{Config.RESET}       : Reproducir en formato NORMAL (Video + Audio)")
        print(f" {Config.BOLD}[Ctrl+A]{Config.RESET}      : Reproducir en formato SÓLO AUDIO")
        print(f" {Config.BOLD}[Ctrl+Y]{Config.RESET}      : Copiar enlace URL al portapapeles")
        print(f" {Config.BOLD}[Ctrl+N]{Config.RESET}      : Realizar una NUEVA BÚSQUEDA")
        print(f" {Config.BOLD}[Ctrl+H]{Config.RESET}      : Mostrar esta ayuda")
        print(f" {Config.BOLD}[Esc]{Config.RESET}         : Salir del programa\n")
        input(f"{Config.DIM}Presiona Enter para continuar...{Config.RESET}")

    @staticmethod
    def prompt_fzf(videos: List[dict]) -> Tuple[str, str]:
        fzf_cmd = [
            "fzf", "--prompt=🔎 Filtrar > ", "--ansi", 
            "--delimiter", r"\|\|", "--with-nth", "2", 
            "--layout=reverse", "--border=rounded", "--info=inline", 
            "--pointer=>", "--expect=ctrl-a,ctrl-y,ctrl-n,ctrl-h"
        ]
        
        terminal_width = shutil.get_terminal_size(fallback=(100, 24)).columns
        dynamic_title_len = max(terminal_width - 44, 35)
        
        lines = [
            f"{i}||{Config.GREEN}{v['duration']:>7}{Config.RESET} {Config.DIM}│{Config.RESET} {Config.YELLOW}{v['uploader'][:20]:<20}{Config.RESET} {Config.DIM}│{Config.RESET} {v['title'][:dynamic_title_len]}" 
            for i, v in enumerate(videos)
        ]
        
        os.system('clear')
        with subprocess.Popen(fzf_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as p:
            out, _ = p.communicate(input="\n".join(lines))
            
        if not out: 
            return "", ""
            
        parts = out.split('\n')
        return parts[0], (parts[1] if len(parts) > 1 else "")