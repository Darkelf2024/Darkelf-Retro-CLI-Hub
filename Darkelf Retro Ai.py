#!/usr/bin/env python3
# Darkelf Retro AI — Enhanced Edition

import os
import sys
import json
import time
import subprocess
import threading
import webbrowser
from collections import deque
from dataclasses import dataclass
from typing import List, Optional

import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt
from rich.spinner import Spinner

# =========================
# GLOBALS & CONFIG
# =========================

APP_NAME = "Darkelf Retro AI"
OLLAMA_MODEL = "llama3"
ARCHIVE_API = "https://archive.org/advancedsearch.php"

console = Console()
ai_memory = deque(maxlen=5)
last_results = []
last_query = None
online = True


# =========================
# BOOT SEQUENCE
# =========================

def boot():
    console.clear()
    banner = """
██████╗  █████╗ ██████╗ ██╗  ██╗███████╗██╗     ███████╗
██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██║     ██╔════╝
██║  ██║███████║██████╔╝█████╔╝ █████╗  ██║     █████╗
██║  ██║██╔══██║██╔══██╗██╔═██╗ ██╔══╝  ██║     ██╔══╝
██████╔╝██║  ██║██║  ██║██║  ██╗███████╗███████╗██║
"""
    console.print(banner, style="bold green")
    for msg in [
        "Initializing CRT interface...",
        "Loading archive intelligence...",
        "Binding AI core...",
        "READY."
    ]:
        console.print(msg)
        time.sleep(0.3)
    time.sleep(0.5)


# =========================
# NETWORK CHECK
# =========================

def check_online():
    global online
    try:
        requests.get("https://archive.org", timeout=3)
        online = True
    except Exception:
        online = False


# =========================
# DATA STRUCTURES
# =========================

@dataclass
class Result:
    title: str
    url: str
    year: Optional[str] = None
    mediatype: Optional[str] = None


# =========================
# ARCHIVE SEARCH
# =========================

def archive_search(query: str, rows=10) -> List[Result]:
    params = {
        "q": query,
        "output": "json",
        "rows": rows,
        "fl[]": ["title", "year", "mediatype", "identifier"]
    }

    r = requests.get(ARCHIVE_API, params=params, timeout=10)
    docs = r.json()["response"]["docs"]

    results = []
    for d in docs:
        results.append(
            Result(
                title=d.get("title", "Unknown"),
                year=d.get("year"),
                mediatype=d.get("mediatype"),
                url=f"https://archive.org/details/{d.get('identifier')}"
            )
        )
    return results


# =========================
# DISPLAY RESULTS
# =========================

def show_results(results: List[Result]):
    table = Table(title="Results", header_style="bold cyan")
    table.add_column("#", style="yellow")
    table.add_column("Title")
    table.add_column("Year")
    table.add_column("Type")

    for i, r in enumerate(results, 1):
        table.add_row(str(i), r.title, str(r.year or ""), r.mediatype or "")

    console.print(table)
    console.print("[dim]Shortcuts: [a] ask AI about item | [o] open | [q] back[/dim]")


# =========================
# AI ENGINE
# =========================

def ai_stream(prompt: str, mode="FREEFORM"):
    identity = f"""
You are Darkelf Retro AI.
Focus on retro computing, emulation, and digital preservation.
Output Mode: {mode}
Be concise, factual, and structured when possible.
"""

    full_prompt = identity + "\n\n" + prompt

    cmd = ["ollama", "run", OLLAMA_MODEL, full_prompt]

    text = Text()
    with Live(text, refresh_per_second=8):
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True
        )
        for line in proc.stdout:
            text.append(line)
    ai_memory.append(prompt)


# =========================
# RESULT → AI HANDOFF
# =========================

def ask_about_result(r: Result):
    mode = Prompt.ask(
        "AI Mode",
        choices=["FREEFORM", "FACT_SHEET", "TIMELINE"],
        default="FACT_SHEET"
    )

    prompt = f"""
Analyze this archival item:

Title: {r.title}
Year: {r.year}
Type: {r.mediatype}
URL: {r.url}

Explain its historical relevance and technical context.
"""
    ai_stream(prompt, mode=mode)


# =========================
# MAIN MENU
# =========================

def main_menu():
    global last_results, last_query

    while True:
        console.print(Panel(
            "[1] Search Internet Archive\n"
            "[2] Ask Retro AI\n"
            "[3] Repeat Last Search\n"
            "[q] Quit",
            title=APP_NAME,
            style="green"
        ))

        choice = Prompt.ask("Select")

        if choice == "1":
            if not online:
                console.print("[red]Offline mode — archive search unavailable[/red]")
                continue

            query = Prompt.ask("Search query")
            last_query = query

            with console.status("Searching archive...", spinner="dots"):
                last_results = archive_search(query)

            show_results(last_results)

            while True:
                cmd = Prompt.ask("Action", default="q")
                if cmd == "q":
                    break
                if cmd == "a":
                    idx = int(Prompt.ask("Item number")) - 1
                    ask_about_result(last_results[idx])
                if cmd == "o":
                    idx = int(Prompt.ask("Item number")) - 1
                    webbrowser.open(last_results[idx].url)

        elif choice == "2":
            q = Prompt.ask("Ask Darkelf Retro AI")
            ai_stream(q)

        elif choice == "3":
            if last_query:
                with console.status("Repeating last search...", spinner="dots"):
                    last_results = archive_search(last_query)
                show_results(last_results)
            else:
                console.print("[dim]No previous search[/dim]")

        elif choice == "q":
            console.print("Goodbye.", style="bold green")
            sys.exit()

        else:
            console.print("[red]Invalid option[/red]")


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    check_online()
    boot()
    main_menu()
