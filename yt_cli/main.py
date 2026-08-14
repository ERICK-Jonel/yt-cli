#!/usr/bin/env python3
import subprocess
import json
import sys
import os
import shutil
import logging
from typing import List, Dict, Tuple, Iterator

# Importación absoluta para que funcione con pipx/paquetes
from yt_cli.config import Config, LoggerSetup, Utils, Spinner

class YouTubeNetwork:
    # ... (Tu clase YouTubeNetwork se queda igual) ...
    @staticmethod
    def search(query: str, limit: int = 40) -> List[Dict[str, str]]:
        logging.info(f"Iniciando búsqueda para: {query}")
        os.system('clear')
        loader = Spinner(f"Buscando '{query}' en YouTube...")
        loader.start()
        
        cmd = ["yt-dlp", f"ytsearch{limit}:{query}", "--print-json", "--flat-playlist", "--quiet", "--no-warnings", "--ignore-errors"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except Exception as e:
            loader.stop()
            print(f"\n{Config.YELLOW}Error al conectar. Revisa {Config.LOG_FILE}.{Config.RESET}")
            sys.exit(1)
        finally:
            loader.stop()

        def _parse_lines(lines: List[str]) -> Iterator[Dict[str, str]]:
            for line in lines:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    raw_duration = data.get("duration_string") or data.get("duration")
                    yield {
                        "title": data.get("title", "Desconocido"), 
                        "uploader": data.get("uploader", data.get("channel", "Desconocido")),
                        "duration": Utils.format_time(raw_duration),
                        "url": data.get("url", data.get("webpage_url", ""))
                    }
                except json.JSONDecodeError: continue
        return list(_parse_lines(result.stdout.split("\n")))

class Player:
    # ... (Tu clase Player se queda igual) ...
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
        if audio_only: cmd.append("--no-video")
        subprocess.run(cmd)

class UI:
    # ... (Tu clase UI se queda igual) ...
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
    def prompt_fzf(videos: List[Dict[str, str]]) -> Tuple[str, str]:
        fzf_cmd = ["fzf", "--prompt=🔎 Filtrar > ", "--ansi", "--delimiter", r"\|\|", "--with-nth", "2", "--layout=reverse", "--border=rounded", "--info=inline", "--pointer=>", "--expect=ctrl-a,ctrl-y,ctrl-n,ctrl-h"]
        terminal_width = shutil.get_terminal_size(fallback=(100, 24)).columns
        dynamic_title_len = max(terminal_width - 44, 35)
        lines = [f"{i}||{Config.GREEN}{v['duration']:>7}{Config.RESET} {Config.DIM}│{Config.RESET} {Config.YELLOW}{v['uploader'][:20]:<20}{Config.RESET} {Config.DIM}│{Config.RESET} {v['title'][:dynamic_title_len]}" for i, v in enumerate(videos)]
        os.system('clear')
        p = subprocess.Popen(fzf_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = p.communicate(input="\n".join(lines))
        if not out: return "", ""
        parts = out.split('\n')
        return parts[0], (parts[1] if len(parts) > 1 else "")

def main() -> None:
    LoggerSetup.init()
    if len(sys.argv) < 2:
        query = input(f"{Config.YELLOW}¿Qué deseas buscar?: {Config.RESET}")
    else:
        query = " ".join(sys.argv[1:])

    # Buscamos UNA VEZ al arrancar o cuando el usuario pide Ctrl+N
    while True:
        videos = YouTubeNetwork.search(query)
        if not videos: break
        
        # Mantenemos esta lista en memoria
        while True:
            key, selected_line = UI.prompt_fzf(videos)
            
            if not key and not selected_line: sys.exit(0)
            if key == "ctrl-h": UI.show_help()
            elif key == "ctrl-n": break # Salimos al bucle superior para buscar de nuevo
            
            elif selected_line:
                idx = int(selected_line.split("||")[0])
                chosen = videos[idx]
                if key == "ctrl-y": Utils.copy_to_clipboard(chosen['url'])
                else: Player.play(chosen, audio_only=(key == "ctrl-a"))

if __name__ == "__main__":
    main()