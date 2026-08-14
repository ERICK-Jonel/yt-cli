#!/usr/bin/env python3
"""
yt-cli - Buscador y Reproductor Minimalista de YouTube por Terminal
====================================================================
Versión estable: columnas en orden lineal (Duración | Canal | Título),
puntero limpio, símbolos musicales y reproductor robusto sin fallos de índice.
"""

import subprocess
import json
import sys
import os
import logging
import threading
import itertools
import time
from typing import List, Dict, Tuple, Iterator

# ==========================================
# MÓDULO 1: CONFIGURACIÓN Y UTILIDADES
# ==========================================
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

class Spinner:
    def __init__(self, message: str = "Cargando..."):
        self.spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.message = message
        self.stop_running = threading.Event()
        self.thread = threading.Thread(target=self._spin)

    def _spin(self):
        while not self.stop_running.is_set():
            sys.stdout.write(f"\r{Config.CYAN}{next(self.spinner)} {Config.BOLD}{self.message}{Config.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()

    def start(self): self.thread.start()
    def stop(self):
        self.stop_running.set()
        self.thread.join()

# ==========================================
# MÓDULO 2: RED Y EXTRACCIÓN (YT-DLP)
# ==========================================
class YouTubeNetwork:
    @staticmethod
    def search(query: str, limit: int = 40) -> List[Dict[str, str]]:
        logging.info(f"Iniciando búsqueda para: {query}")
        os.system('clear')
        
        loader = Spinner(f"Buscando '{query}' en YouTube...")
        loader.start()
        
        cmd = [
            "yt-dlp",
            f"ytsearch{limit}:{query}",
            "--print-json",
            "--flat-playlist", 
            "--quiet",
            "--no-warnings",
            "--ignore-errors"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logging.info("Extracción de red finalizada.")
        except Exception as e:
            loader.stop()
            logging.critical(f"Fallo crítico en yt-dlp: {e}")
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
                except json.JSONDecodeError:
                    continue

        return list(_parse_lines(result.stdout.split("\n")))

# ==========================================
# MÓDULO 3: REPRODUCTOR MULTIMEDIA (MPV)
# ==========================================
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
        
        print(f" {Config.GREEN}[ Estado ]{Config.RESET} Reproduciendo contenido (mpv)...")
        print(f" {Config.DIM}Controles: [Espacio] Pausa | [9/0] Volumen | [q] Cerrar{Config.RESET}")
        print(f"{color}{Config.BOLD}======================================================================{Config.RESET}\n")
        
        cmd = ["mpv", video_data['url'], "--ytdl-raw-options=cookies-from-browser=firefox"]
        if audio_only:
            cmd.append("--no-video")
            
        try:
            subprocess.run(cmd)
            logging.info(f"Reproducción finalizada: {video_data['url']}")
        except Exception as e:
            logging.error(f"Fallo al ejecutar mpv: {e}")
            print(f"{Config.YELLOW}Error al lanzar el reproductor mpv.{Config.RESET}")

# ==========================================
# MÓDULO 4: INTERFAZ DE USUARIO (FZF)
# ==========================================
class UI:
    @staticmethod
    def show_help() -> None:
        os.system('clear')
        print(f"{Config.CYAN}{Config.BOLD}=== ♫ yt-cli : Manual de Usuario ==={Config.RESET}\n")
        print(f"{Config.YELLOW}Navegación en la Lista (FZF):{Config.RESET}")
        print(f" {Config.BOLD}[Escribir]{Config.RESET} : Filtrar resultados en tiempo real")
        print(f" {Config.BOLD}[Enter]{Config.RESET}    : Reproducir en formato NORMAL (Video + Audio)")
        print(f" {Config.BOLD}[Ctrl+A]{Config.RESET}   : Reproducir en formato SÓLO AUDIO")
        print(f" {Config.BOLD}[Ctrl+N]{Config.RESET}   : Realizar una NUEVA BÚSQUEDA")
        print(f" {Config.BOLD}[Ctrl+H]{Config.RESET}   : Mostrar esta ayuda")
        print(f" {Config.BOLD}[Esc]{Config.RESET}      : Salir del programa\n")
        input(f"{Config.DIM}Presiona Enter para continuar...{Config.RESET}")

    @staticmethod
    def prompt_fzf(videos: List[Dict[str, str]]) -> Tuple[str, str]:
        fzf_cmd = [
            "fzf", 
            "--prompt=🔎 Filtrar > ", 
            "--ansi", 
            "--delimiter", r"\|\|", 
            "--with-nth", "2",          # Muestra exactamente la columna visual y mantiene el índice oculto intacto
            "--layout=reverse", 
            "--border=rounded",       
            "--info=inline",          
            "--pointer=>",            
            "--expect=ctrl-a,ctrl-n,ctrl-h" 
        ]

        def _generate_lines() -> Iterator[str]:
            for i, v in enumerate(videos):
                # Orden lineal perfecto: Duración | Canal | Título
                duration = f"{Config.GREEN}{v['duration']:>7}{Config.RESET}"
                uploader = f"{Config.YELLOW}{v['uploader'][:18]:<18}{Config.RESET}"
                title = f"{v['title'][:48]:<48}"
                
                visual = f"{duration} {Config.DIM}│{Config.RESET} {uploader} {Config.DIM}│{Config.RESET} {title}"
                
                # Estructura limpia: [0: ID] || [1: Visual]
                yield f"{i}||{visual}"

        os.system('clear')
        logging.info("Lanzando instancia interactiva de FZF.")
        
        p = subprocess.Popen(fzf_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        out, _ = p.communicate(input="\n".join(_generate_lines()))
        
        if not out:
            return "", "" 
            
        parts = out.split('\n')
        key_pressed = parts[0] 
        selected_line = parts[1] if len(parts) > 1 else ""
        
        if not key_pressed and not selected_line.strip():
            return "", ""
            
        return key_pressed, selected_line

# ==========================================
# PUNTO DE ENTRADA PRINCIPAL
# ==========================================
def main() -> None:
    LoggerSetup.init()
    
    if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
        UI.show_help()
        sys.exit(0)

    try:
        logging.info("--- Iniciando ciclo de vida yt-cli ---")
        os.system('clear')
        
        if len(sys.argv) < 2:
            print(f"{Config.CYAN}{Config.BOLD}yt-cli ♫ Minimal{Config.RESET}")
            query = input(f"{Config.YELLOW}¿Qué deseas buscar?: {Config.RESET}")
            if not query.strip(): sys.exit(0)
        else:
            query = " ".join(sys.argv[1:])

        while True: 
            videos = YouTubeNetwork.search(query)
            
            if not videos:
                query = input(f"{Config.YELLOW}Sin resultados. Intenta otra búsqueda (Enter para salir): {Config.RESET}")
                if not query.strip(): break
                continue

            while True:
                key, selected_line = UI.prompt_fzf(videos)
                
                if not key and not selected_line:
                    os.system('clear')
                    sys.exit(0)
                
                if key == "ctrl-h":
                    UI.show_help()
                    continue 
                    
                if key == "ctrl-n":
                    os.system('clear')
                    new_query = input(f"{Config.YELLOW}Nueva búsqueda (Enter para cancelar): {Config.RESET}")
                    if new_query.strip():
                        query = new_query
                        break 
                    continue

                if selected_line:
                    try:
                        selected_index = int(selected_line.split("||")[0])
                        chosen_video = videos[selected_index]
                        is_audio_only = (key == "ctrl-a")
                        
                        Player.play(chosen_video, audio_only=is_audio_only)
                        
                    except (ValueError, IndexError):
                        logging.error("Error al decodificar la selección de FZF.")
                        continue

    except KeyboardInterrupt:
        os.system('clear')
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Excepción general no capturada: {e}")
        print(f"\n{Config.YELLOW}Ocurrió un error fatal. Revisa {Config.LOG_FILE}{Config.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()