#!/usr/bin/env python3
"""
yt-cli - Buscador y Reproductor Minimalista de YouTube por Terminal
====================================================================
Versión refactorizada con arquitectura modular, tipado estático,
evaluación perezosa (streams) y controles avanzados en FZF.
"""

import subprocess
import json
import sys
import os
import logging
from typing import List, Dict, Optional, Tuple, Iterator

# ==========================================
# MÓDULO 1: CONFIGURACIÓN Y UTILIDADES
# ==========================================
class Config:
    """Almacena constantes y configuraciones globales del sistema."""
    LOG_FILE: str = "/tmp/yt-cli.log"
    
    # Códigos de color ANSI
    RESET: str  = "\033[0m"
    CYAN: str   = "\033[96m"
    GREEN: str  = "\033[92m"
    YELLOW: str = "\033[93m"
    DIM: str    = "\033[2m"

class LoggerSetup:
    """Maneja la inicialización del registro de eventos (Logs)."""
    @staticmethod
    def init() -> None:
        logging.basicConfig(
            filename=Config.LOG_FILE,
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - [%(module)s] %(message)s"
        )

class Utils:
    """Funciones puras de utilidad general."""
    @staticmethod
    def format_time(duration: any) -> str:
        """Convierte segundos crudos al formato estándar MM:SS o HH:MM:SS."""
        if isinstance(duration, (int, float)):
            m, s = divmod(int(duration), 60)
            h, m = divmod(m, 60)
            return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"
        return str(duration) if duration else "0:00"

# ==========================================
# MÓDULO 2: RED Y EXTRACCIÓN (YT-DLP)
# ==========================================
class YouTubeNetwork:
    """Encapsula toda la lógica de conexión y extracción de metadatos de YouTube."""
    
    @staticmethod
    def search(query: str, limit: int = 40) -> List[Dict[str, str]]:
        """
        Ejecuta la búsqueda en yt-dlp y retorna los resultados parseados.
        Utiliza evaluación perezosa en el parseo JSON.
        """
        logging.info(f"Iniciando búsqueda para: {query}")
        print(f"{Config.CYAN}>> Buscando '{query}' en YouTube...{Config.RESET}")
        
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
            logging.critical(f"Fallo crítico en yt-dlp: {e}")
            print(f"{Config.YELLOW}Error al conectar. Revisa {Config.LOG_FILE}.{Config.RESET}")
            sys.exit(1)

        # Generador interno para evaluación perezosa del volcado JSON
        def _parse_lines(lines: List[str]) -> Iterator[Dict[str, str]]:
            for line in lines:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    raw_duration = data.get("duration_string") or data.get("duration")
                    yield {
                        "title": data.get("title", "Desconocido")[:55], 
                        "uploader": data.get("uploader", data.get("channel", "Desconocido"))[:15],
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
    """Controlador para el subsistema de reproducción MPV."""
    
    @staticmethod
    def play(video_data: Dict[str, str], audio_only: bool = False) -> None:
        """
        Lanza MPV en primer plano con soporte de cookies del navegador
        para evitar el bloqueo anti-bot de YouTube.
        """
        os.system('clear')
        mode_text = "SÓLO AUDIO" if audio_only else "VIDEO"
        
        print(f"{Config.GREEN}>> Reproduciendo ({mode_text}):{Config.RESET} {video_data['title']}")
        print(f"{Config.DIM}Enlace: {video_data['url']}{Config.RESET}\n")
        
        cmd = ["mpv", video_data['url']]
        
        # Inyectamos las cookies de Firefox de forma nativa para saltar el bloqueo anti-bot
        cmd.extend([
            "--ytdl-raw-options=cookies-from-browser=firefox"
        ])
        
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
    """Maneja la vista y la interacción del usuario mediante TUI y atajos."""
    
    @staticmethod
    def show_help() -> None:
        """Despliega la ayuda estructurada en pantalla."""
        os.system('clear')
        print(f"{Config.CYAN}=== yt-cli : Manual de Usuario ==={Config.RESET}\n")
        
        print(f"{Config.YELLOW}Navegación en la Lista (FZF):{Config.RESET}")
        print(" [Enter]   : Reproducir en formato NORMAL (Video + Audio)")
        print(" [Ctrl+A]  : Reproducir en formato SÓLO AUDIO (Ahorra CPU/RAM)")
        print(" [Ctrl+N]  : Realizar una NUEVA BÚSQUEDA")
        print(" [Ctrl+H]  : Mostrar esta ayuda")
        print(" [Esc]     : Salir del programa\n")
        
        print(f"{Config.YELLOW}Controles de MPV (Durante reproducción):{Config.RESET}")
        print(" [9] / [0] : Bajar / Subir volumen")
        print(" [m]       : Silenciar (Mute)")
        print(" [Espacio] : Pausar / Reanudar")
        print(" [f]       : Pantalla completa (Fullscreen)")
        print(" [q]       : Cerrar video y volver a la lista")
        
        input(f"\n{Config.DIM}Presiona Enter para continuar...{Config.RESET}")

    @staticmethod
    def prompt_fzf(videos: List[Dict[str, str]]) -> Tuple[str, str]:
        """
        Genera el menú interactivo FZF utilizando un stream I/O no bloqueante.
        Retorna la tecla presionada (Expect Key) y el índice seleccionado.
        """
        fzf_cmd = [
            "fzf", 
            "--prompt=Seleccionar > ", 
            "--ansi", 
            "--delimiter", r"\|\|", 
            "--with-nth", "2..",
            "--layout=reverse", 
            "--border",
            "--expect=ctrl-a,ctrl-n,ctrl-h" 
        ]

        def _generate_lines() -> Iterator[str]:
            for i, v in enumerate(videos):
                yield f"{i}||{v['title']:<58} {Config.DIM}|{Config.RESET} {Config.GREEN}{v['duration']:<6}{Config.RESET} {Config.DIM}|{Config.RESET} {Config.YELLOW}{v['uploader']:<15}{Config.RESET}"

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
# PUNTO DE ENTRADA PRINCIPAL (MAIN LOOP)
# ==========================================
def main() -> None:
    LoggerSetup.init()
    
    if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"]:
        UI.show_help()
        sys.exit(0)

    try:
        logging.info("--- Iniciando ciclo de vida yt-cli ---")
        
        if len(sys.argv) < 2:
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
                    print(f"{Config.DIM}Saliendo de yt-cli...{Config.RESET}")
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
        print(f"\n{Config.DIM}Interrupción manual (Ctrl+C). Saliendo...{Config.RESET}")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Excepción general no capturada: {e}")
        print(f"\n{Config.YELLOW}Ocurrió un error fatal. Revisa {Config.LOG_FILE}{Config.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()