#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import textwrap
import subprocess
import requests
import hashlib
import zlib
from shutil import which
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


# ============================================================
# CONFIG
# ============================================================

APP_NAME = "Darkelf Retro CLI"
APP_VERSION = "4.4"

DDG_LITE = "https://lite.duckduckgo.com/lite/?q="
DEFAULT_MODEL = "mistral"
USER_AGENT = "DarkelfRetro/4.4"

HOME = os.path.expanduser("~")
BASE_DIR = os.path.join(HOME, ".darkelf_retro")
HISTORY_FILE = os.path.join(BASE_DIR, "search_history.json")

IA_ADV_SEARCH = "https://archive.org/advancedsearch.php"
IA_METADATA = "https://archive.org/metadata/"
VGHF_SEARCH = "https://library.gamehistory.org/"

os.makedirs(BASE_DIR, exist_ok=True)

console = Console()

# ============================================================
# ROM CONFIG
# ============================================================

ROM_CACHE_DIR = os.path.join(BASE_DIR, "rom_cache")
os.makedirs(ROM_CACHE_DIR, exist_ok=True)

ROM_EXTENSIONS = (
    ".iso", ".bin", ".cue", ".chd", ".cso",
    ".zip", ".7z", ".rar",
    ".nes", ".sfc", ".smc",
    ".gb", ".gbc", ".gba",
    ".n64", ".z64", ".v64",
    ".gcm", ".wbfs", ".wad",
    ".md", ".gen", ".sms",
    ".fds", ".a26", ".a78",
)

# ============================================================
# UTIL
# ============================================================

def wrap(text: str, width: int = 96) -> str:
    return "\n".join(textwrap.wrap(text, width))

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def press_enter(msg="Press Enter to continue..."):
    input(f"\n{msg}")

def is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except Exception:
        return False
        
# ============================================================
# ADD: ROM HASHING (CRC32 / MD5 / SHA1)
# ============================================================

def hash_rom_file(path, blocksize=1024 * 1024):
    crc = 0
    with open(path, "rb") as f:
        while True:
            chunk = f.read(blocksize)
            if not chunk:
                break
            crc = zlib.crc32(chunk, crc)
    return f"{crc & 0xffffffff:08X}"

# ============================================================
# ROM + PLATFORM DETECTION
# ============================================================

PLATFORM_KEYWORDS = {
    "PS2": ["ps2", "playstation 2"],
    "PS1": ["psx", "ps1", "playstation"],
    "GAMECUBE": ["gamecube", "gc"],
    "WII": ["wii"],
    "DREAMCAST": ["dreamcast", "dc"],
    "SATURN": ["saturn"],
    "PSP": ["psp"],
}

def detect_platform(name: str, path: str | None = None):
    lname = name.lower()

    # --- Header-based detection (best)
    if path and os.path.isfile(path):
        try:
            with open(path, "rb") as f:
                header = f.read(0x20)

            # GameCube discs contain "DVDMAGIC" at 0x1C
            if b"DVDMAGIC" in header:
                return "GAMECUBE"
        except Exception:
            pass

    # --- Size heuristic fallback
    if path and os.path.isfile(path):
        try:
            size_gb = os.path.getsize(path) / (1024 ** 3)

            # GameCube discs are ~1.35GB
            if size_gb < 1.6:
                return "GAMECUBE"

            # PS2 DVDs are usually > 2GB
            if size_gb >= 2.0:
                return "PS2"
        except Exception:
            pass

    # --- Filename keywords (last resort)
    for plat, keys in PLATFORM_KEYWORDS.items():
        if any(k in lname for k in keys):
            return plat

    return "UNKNOWN"

def scan_roms(path: str):
    roms = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith(ROM_EXTENSIONS):
                roms.append(os.path.join(root, f))
    return roms

def rom_metadata(path: str):
    return {
        "file": os.path.basename(path),
        "platform": detect_platform(os.path.basename(path), path),
        "size_mb": round(os.path.getsize(path) / 1024 / 1024, 2),
        "path": path
    }
    
def should_hash(path, max_mb=500):
    try:
        size_mb = os.path.getsize(path) / 1024 / 1024
        return size_mb <= max_mb
    except Exception:
        return False

# ============================================================
# ADD: EXTENDED ROM METADATA (OPTIONAL)
# ============================================================

def rom_metadata_extended(path: str):
    meta = rom_metadata(path).copy()
    try:
        meta["crc32"] = hash_rom_file(path)
    except Exception as e:
        meta["crc32"] = "ERROR"
    return meta

# ============================================================
# ANDROID DEVICE DETECTION (ADB)
# ============================================================

def adb_detect():
    try:
        out = subprocess.check_output(
            ["adb", "shell", "getprop"],
            stderr=subprocess.DEVNULL,
            text=True
        )

        def prop(k):
            for line in out.splitlines():
                if k in line:
                    return line.split(":")[-1].strip(" []")
            return "Unknown"

        return {
            "device": prop("ro.product.model"),
            "cpu": prop("ro.board.platform"),
            "serial": prop("ro.serialno")
        }
    except Exception:
        return {
            "device": "ADB not detected",
            "cpu": "Unknown",
            "serial": "N/A"
        }

# ============================================================
# OLLAMA BACKGROUND MANAGER (ONE TERMINAL)
# ============================================================

class OllamaManager:
    """
    Ensures Ollama daemon is available.
    If not running, starts `ollama serve` detached from this process
    so it survives terminal/app exit (best-effort across OSes).
    """
    def __init__(self):
        self.started_here = False

    def is_running(self) -> bool:
        try:
            p = subprocess.run(
                ["ollama", "list"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2.5
            )
            return p.returncode == 0
        except Exception:
            return False

    def _start_detached(self):
        # Cross-platform detachment:
        # - Windows: DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP
        # - POSIX: start_new_session=True (similar to setsid)
        if os.name == "nt":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            return subprocess.Popen(
                ["ollama", "serve"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
        else:
            return subprocess.Popen(
                ["ollama", "serve"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True
            )

    def ensure_running(self):
        if not which("ollama"):
            console.print(Panel(
                "Ollama engine not found.\nInstall from https://ollama.com",
                title="Darkelf Retro AI Error",
                border_style="red"
            ))
            sys.exit(1)

        # Already running?
        if self.is_running():
            return

        # Start daemon detached
        try:
            self._start_detached()
            self.started_here = True
        except Exception as e:
            console.print(Panel(
                f"Failed to start Ollama server.\n{e}",
                title="Darkelf Retro AI Error",
                border_style="red"
            ))
            sys.exit(1)

        # Wait until it is actually ready (instead of a blind sleep)
        t0 = time.time()
        while time.time() - t0 < 10.0:
            if self.is_running():
                return
            time.sleep(0.25)

        console.print(Panel(
            "Ollama was started but did not become ready within 10 seconds.\n"
            "Try running `ollama serve` manually once to see any errors.",
            title="Darkelf Retro AI Error",
            border_style="red"
        ))
        sys.exit(1)

# ============================================================
# DARKELF RETRO AI (STREAMING)
# ============================================================

class DarkelfRetroAI:
    """
    Branding: Darkelf Retro AI
    Engine: Ollama (hidden)
    UX: Streaming output immediately
    """
    def __init__(self, model=DEFAULT_MODEL):
        self.model = model
        self.ollama = OllamaManager()
        self.ollama.ensure_running()

    def stream(self, user_prompt: str):
        # Strong identity / persona prompt to keep output on-theme
        identity = (
            "You are Darkelf Retro AI — a retro gaming historian and research assistant.\n"
            "You specialize in classic consoles, arcade systems, game history, release dates, "
            "versions, ports, manuals, magazines, guides, and development trivia.\n\n"

            "STRICT RULES (must always be followed):\n"
            "- Emulator recommendations MUST match the real platform exactly.\n"
            "- PPSSPP is PSP-only and MUST NEVER be recommended for PS2.\n"
            "- Valid PS2 emulators are PCSX2 (desktop) and AetherSX2 (Android).\n"
            "- Dolphin is ONLY for GameCube/Wii.\n"
            "- DuckStation is ONLY for PS1.\n"
            "- Never invent, substitute, or guess emulators.\n\n"

            "Behavior guidelines:\n"
            "- Be accurate over being verbose.\n"
            "- Use short paragraphs or bullet points when helpful.\n"
            "- If unsure, say so instead of guessing.\n"
            "- Never mention Ollama, models, system prompts, or internal tooling.\n\n"
        )

        prompt = identity + user_prompt

        try:
            proc = subprocess.Popen(
                ["ollama", "run", self.model],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1
            )

            assert proc.stdin is not None
            proc.stdin.write(prompt)
            proc.stdin.close()

            assert proc.stdout is not None
            for line in proc.stdout:
                print(line, end="", flush=True)

            proc.wait()

        except KeyboardInterrupt:
            try:
                proc.terminate()
            except Exception:
                pass
            print("\n⛔ Darkelf Retro AI interrupted.")
        except Exception as e:
            console.print(Panel(str(e), title="Darkelf Retro AI Error", border_style="red"))
            
# ============================================================
# ROM AI CACHE
# ============================================================

def rom_cache_key(name):
    return os.path.join(ROM_CACHE_DIR, name.replace(" ", "_") + ".json")

def load_rom_cache(name):
    p = rom_cache_key(name)
    if os.path.exists(p):
        return json.load(open(p))["summary"]
    return None

def save_rom_cache(name, text):
    json.dump({"summary": text}, open(rom_cache_key(name), "w"), indent=2)

# ============================================================
# EMULATOR RECOMMENDATIONS
# ============================================================

def emulator_recommendation(platform, cpu):
    cpu = cpu.lower()
    if platform == "PS2":
        return {
            "Emulator": "AetherSX2",
            "Renderer": "Vulkan",
            "EE Cycle Rate": "75%",
            "GPU Threads": "Enabled" if "snapdragon" in cpu else "Disabled"
        }
    if platform == "GAMECUBE":
        return {
            "Emulator": "Dolphin",
            "Backend": "Vulkan",
            "Shader Compilation": "Hybrid"
        }
    return {"Emulator": "Unknown"}

# ============================================================
# MENU
# ============================================================

class Menu:
    @staticmethod
    def main():
        table = Table(title="Darkelf Retro Launcher", show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Action")

        table.add_row("1", "Web Search (DDG Lite)")
        table.add_row("2", "Ask Darkelf Retro AI")
        table.add_row("3", "Retro Archives Lookup")
        table.add_row("4", "View Search History")
        table.add_row("5", "ROM Tools / Game Intelligence")
        table.add_row("6", "Help / Hotkeys")
        table.add_row("7", "Batch ROM Scan")
        table.add_row("0", "Exit")

        console.print(table)

    @staticmethod
    def help():
        console.print(Panel(
            "\n".join([
                "Hotkeys / Tips:",
                "• In lists, type a number (e.g., 1) to open that item.",
                "• Web Search: use DDG Lite to find guides, wikis, manuals, maps.",
                "• Archives: searches Internet Archive (magazines, guides, manuals, ephemera).",
                "• VGHF: opens a browser-style search via DDG for the VGHF library.",
                "",
                "Darkelf Retro AI Tips:",
                "• Ask for release dates, dev trivia, ports, versions, region differences.",
                "• Ask for 'beginner route', 'best starter loadout', 'boss tips', etc.",
            ]),
            title="Help",
            border_style="cyan"
        ))

# ============================================================
# SEARCH ENGINE (DDG Lite)
# ============================================================

class WebSearch:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.history = self._load_history()

    def _load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                return json.load(open(HISTORY_FILE, "r", encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            json.dump(self.history[-200:], open(HISTORY_FILE, "w", encoding="utf-8"), indent=2)
        except Exception:
            pass

    def search(self, query: str, max_results: int = 12):
        self.history.append({"q": query, "ts": int(time.time())})
        self._save_history()

        url = DDG_LITE + requests.utils.quote(query)
        html = self.session.get(url, timeout=15).text
        soup = BeautifulSoup(html, "html.parser")

        results = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text(" ", strip=True)
            if not title:
                continue
            if "uddg=" not in href:
                continue
            try:
                real = requests.utils.unquote(href.split("uddg=")[1].split("&")[0])
            except Exception:
                continue
            results.append((title, real))
            if len(results) >= max_results:
                break
        return results

# ============================================================
# INTERNET ARCHIVE (official JSON search + metadata)
# ============================================================

class InternetArchive:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def advanced_search(self, q: str, rows: int = 12, page: int = 1, fields=None):
        if fields is None:
            fields = ["identifier", "title", "mediatype", "date", "creator", "downloads"]

        params = {
            "q": q,
            "fl[]": fields,
            "rows": rows,
            "page": page,
            "output": "json",
        }
        r = self.session.get(IA_ADV_SEARCH, params=params, timeout=20)
        r.raise_for_status()
        return r.json()

    def get_metadata(self, identifier: str):
        r = self.session.get(IA_METADATA + identifier, timeout=20)
        r.raise_for_status()
        return r.json()

# ============================================================
# APP
# ============================================================

class DarkelfCLI:
    def __init__(self):
        self.ai = DarkelfRetroAI()
        self.searcher = WebSearch()
        self.ia = InternetArchive()

        self.last_web_results = []
        self.last_archive_results = []  # list of dicts
        self.last_query = ""

    def banner(self):
        console.print(Panel.fit(
            f"[bold green]{APP_NAME}[/bold green] v{APP_VERSION}\n"
            "🎮 Retro Gaming Research Terminal\n"
            "🤖 Darkelf Retro AI (local, live)\n"
            "🗄️ Archives: Internet Archive + VGHF",
            border_style="green"
        ))

    # -----------------------
    # UI helpers
    # -----------------------
    def show_results_table(self, title: str, rows):
        table = Table(title=title, show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Title", style="white")
        table.add_column("URL", style="dim")

        for i, (t, u) in enumerate(rows, 1):
            table.add_row(str(i), t[:80], u[:90])
        console.print(table)

    def show_archive_table(self, title: str, docs):
        table = Table(title=title, show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Title", style="white")
        table.add_column("Type", style="green", width=10)
        table.add_column("Year", style="dim", width=8)
        table.add_column("ID", style="dim")

        for i, d in enumerate(docs, 1):
            t = (d.get("title") or d.get("identifier") or "")[:70]
            mt = (d.get("mediatype") or "")[:10]
            year = (str(d.get("date") or "")[:4]) if d.get("date") else ""
            ident = d.get("identifier", "")
            table.add_row(str(i), t, mt, year, ident)
        console.print(table)

    # -----------------------
    # Web Search flow
    # -----------------------
    def web_search_flow(self):
        clear()
        self.banner()
        q = input("Web search for> ").strip()
        if not q:
            return
        self.last_query = q
        results = self.searcher.search(q, max_results=12)
        self.last_web_results = results
        if not results:
            console.print("No results.")
            press_enter()
            return

        self.show_results_table(f"DDG Lite Results: {q}", results)

        sel = input("\nOpen # (or Enter to go back)> ").strip()
        if sel == "":
            return
        if is_int(sel):
            idx = int(sel) - 1
            if 0 <= idx < len(results):
                title, url = results[idx]
                clear()
                self.banner()
                console.print(Panel(url, title=title, border_style="green"))
                press_enter("Press Enter to return to menu...")
            else:
                console.print("Invalid selection.")
                press_enter()

    # -----------------------
    # AI flow
    # -----------------------
    def ai_flow(self):
        clear()
        self.banner()
        q = input("Ask Darkelf Retro AI> ").strip()
        if not q:
            return
        clear()
        self.banner()
        console.print(Panel(
            f"[bold]Q:[/bold] {q}\n\n[dim]Darkelf Retro AI is responding…[/dim]",
            title=f"Darkelf Retro AI ({self.ai.model})",
            border_style="magenta"
        ))
        self.ai.stream(q)
        press_enter("Press Enter to return to menu...")
        
    # -----------------------
    # ADD: Batch ROM Scan
    # -----------------------
    def batch_rom_scan(self):
        clear()
        self.banner()
        path = input("ROM directory to scan> ").strip()
        roms = scan_roms(path)

        if not roms:
            console.print("No ROMs found.")
            press_enter()
            return

        table = Table(title="Batch ROM Scan")
        table.add_column("File")
        table.add_column("Platform", justify="center")
        table.add_column("Size (GB)", justify="right")
        table.add_column("CRC32")

        for idx, r in enumerate(roms, 1):
            console.print(f"[dim]Hashing ({idx}/{len(roms)}): {os.path.basename(r)}[/dim]")

            meta = rom_metadata_extended(r)
            size_gb = os.path.getsize(r) / (1024 ** 3)

            table.add_row(
                meta["file"],
                meta["platform"],
                f"{size_gb:.2f}",
                meta.get("crc32", "N/A")
            )


        console.print(table)
        press_enter()

    # -----------------------
    # Archives flow
    # -----------------------
    def archives_flow(self):
        clear()
        self.banner()

        table = Table(title="Retro Archives Lookup", show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Mode", style="white")
        table.add_column("What you get", style="dim")

        table.add_row("1", "Internet Archive: Manuals / Guides", "Strategy guides, manuals, walkthrough books, scans")
        table.add_row("2", "Internet Archive: Magazines", "EGM/GamePro/etc. issues, scans, articles")
        table.add_row("3", "Internet Archive: Press / Promo", "Press kits, promo CDs, marketing materials (varies)")
        table.add_row("4", "VGHF Library (open via web search)", "Search the VGHF catalog & digital archive")
        table.add_row("0", "Back", "Return to main menu")
        console.print(table)

        mode = input("\nSelect> ").strip()
        if mode == "0" or mode == "":
            return

        term = input("Game / topic> ").strip()
        if not term:
            return

        if mode == "4":
            # Use DDG Lite to discover VGHF results
            q = f"site:library.gamehistory.org {term}"
            clear()
            self.banner()
            results = self.searcher.search(q, max_results=12)
            self.last_web_results = results
            if not results:
                console.print("No results.")
                press_enter()
                return
            self.show_results_table(f"VGHF Results: {term}", results)
            press_enter("Press Enter to return to Archives menu...")
            return

        # Internet Archive query builder
        if mode == "1":
            ia_q = f'({term}) AND (manual OR "instruction manual" OR "strategy guide" OR walkthrough) AND (mediatype:texts)'
            label = "Internet Archive — Manuals / Guides"
        elif mode == "2":
            ia_q = f'({term}) AND (magazine OR "Electronic Gaming Monthly" OR GamePro OR "Nintendo Power") AND (mediatype:texts)'
            label = "Internet Archive — Magazines"
        elif mode == "3":
            ia_q = f'({term}) AND (presskit OR "press kit" OR promo OR "press cd" OR "press disc")'
            label = "Internet Archive — Press / Promo"
        else:
            console.print("Invalid selection.")
            press_enter()
            return

        clear()
        self.banner()
        console.print(Panel(
            f"Searching Internet Archive…\n\n[dim]{ia_q}[/dim]",
            title=label,
            border_style="yellow"
        ))

        try:
            data = self.ia.advanced_search(ia_q, rows=12, page=1)
            docs = data.get("response", {}).get("docs", [])
            self.last_archive_results = docs
        except Exception as e:
            console.print(Panel(str(e), title="Archive Error", border_style="red"))
            press_enter()
            return

        if not self.last_archive_results:
            console.print("No archive hits found.")
            press_enter()
            return

        self.show_archive_table(f"{label}: {term}", self.last_archive_results)

        sel = input("\nOpen metadata # (or Enter to go back)> ").strip()
        if sel == "":
            return
        if not is_int(sel):
            console.print("Enter a number.")
            press_enter()
            return

        idx = int(sel) - 1
        if not (0 <= idx < len(self.last_archive_results)):
            console.print("Invalid selection.")
            press_enter()
            return

        ident = self.last_archive_results[idx].get("identifier")
        if not ident:
            console.print("Missing identifier.")
            press_enter()
            return

        clear()
        self.banner()
        console.print(Panel(
            f"https://archive.org/details/{ident}\n\nFetching item metadata…",
            title="Opening Internet Archive Item",
            border_style="yellow"
        ))

        try:
            md = self.ia.get_metadata(ident)
        except Exception as e:
            console.print(Panel(str(e), title="Metadata Error", border_style="red"))
            press_enter()
            return

        meta = md.get("metadata", {}) or {}
        title = meta.get("title", ident)
        desc = meta.get("description", "")
        creator = meta.get("creator", "")
        date = meta.get("date", "")
        mediatype = meta.get("mediatype", "")

        body = "\n".join([
            f"[bold]Title:[/bold] {title}",
            f"[bold]Type:[/bold] {mediatype}",
            f"[bold]Creator:[/bold] {creator}",
            f"[bold]Date:[/bold] {date}",
            "",
            "[bold]Item Page:[/bold] " + f"https://archive.org/details/{ident}",
            "",
            "[bold]Description:[/bold]",
            wrap(str(desc), 92) if desc else "(none)",
        ])
        console.print(Panel(body, title="Archive Item", border_style="yellow"))
        press_enter("Press Enter to return...")
        
    # -----------------------
    # ROM FLOW
    # -----------------------
    def rom_flow(self):
        clear()
        self.banner()
        path = input("ROM directory> ").strip()
        roms = scan_roms(path)

        if not roms:
            console.print("No ROMs found.")
            press_enter()
            return

        for i, r in enumerate(roms, 1):
            console.print(f"[{i}] {os.path.basename(r)}")

        sel = input("\nSelect ROM #> ").strip()
        if not is_int(sel):
            return

        rom = rom_metadata(roms[int(sel) - 1])
        device = adb_detect()

        cached = load_rom_cache(rom["file"])
        if cached:
            console.print(Panel(wrap(cached), title="Cached Game Intelligence"))
        else:
            prompt = f"""
Analyze this ROM and provide:
- Game title
- Platform
- Release year
- Developer
- Emulator recommendation (must match platform exactly; do NOT invent or substitute emulators)
- Performance tips

ROM: {rom}
Android Device: {device}
"""
            clear()
            self.banner()
            self.ai.stream(prompt)
            text = input("\n\nSave summary? (y/n)> ").lower()
            if text == "y":
                save_rom_cache(rom["file"], prompt)

        cfg = emulator_recommendation(rom["platform"], device["cpu"])
        table = Table(title="Emulator Recommendation")
        table.add_column("Setting")
        table.add_column("Value")
        for k, v in cfg.items():
            table.add_row(k, v)
        console.print(table)
        press_enter()

    # -----------------------
    # -----------------------
    # History flow
    # -----------------------
    def history_flow(self):
        clear()
        self.banner()
        hist = self.searcher.history[-25:]
        if not hist:
            console.print("No history yet.")
            press_enter()
            return

        table = Table(title="Search History (latest)", show_lines=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("When", style="dim", width=26)
        table.add_column("Query", style="white")

        for i, h in enumerate(reversed(hist), 1):
            when = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(h["ts"]))
            table.add_row(str(i), when, h["q"])
        console.print(table)
        press_enter()

    def run(self):
        while True:
            clear()
            self.banner()
            Menu.main()
            choice = input("\nSelect> ").strip()

            if choice == "0":
                break

            elif choice == "1":
                self.web_search_flow()

            elif choice == "2":
                self.ai_flow()

            elif choice == "3":
                self.archives_flow()

            elif choice == "4":
                self.history_flow()

            elif choice == "5":
                self.rom_flow()

            elif choice == "6":
                clear()
                self.banner()
                Menu.help()
                press_enter()

            elif choice == "7":
                self.batch_rom_scan()

            else:
                console.print("Invalid selection.")
                press_enter()

# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    DarkelfCLI().run()
