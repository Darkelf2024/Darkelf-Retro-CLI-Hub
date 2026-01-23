# Darkelf Retro CLI Tools

Darkelf Retro CLI is a local-first, terminal-based retro gaming research environment. Designed for historians, collectors, and enthusiasts, it provides fast, focused access to classic game information directly from the command line.

This tool combines text-based web search, official retro game archives, and a local streaming AI assistant called **Darkelf Retro AI**, delivering a seamless terminal experience for retro gaming research.

---

## Features

### Retro Gaming Research
- **Web Search**: DuckDuckGo Lite integration for clean, text-only results.
- **Navigation**: Simple number-based navigation.
- **Search History**: Persistent local history for efficient revisits.

### Darkelf Retro AI
- **AI Integration**: Fully local AI powered by **Ollama**.
- **Focused Responses**: Streaming insights tailored to retro consoles, arcade systems, manuals, magazines, and game history.
- **Terminal-First**: Runs within the same terminal session.

### Retro Game Archives
- **Internet Archive**: Access manuals, guides, and magazines from the Internet Archive.
- **Video Game History Foundation**: Discover metadata and research from the VGHF catalog.
- **Ethical Use**: Metadata and research only—no ROM downloads.

---

## Design Philosophy

**Darkelf Retro CLI** adheres to a local-first, terminal-native approach, prioritizing clarity, research, and respect for archival sources. 

This tool is for serious retro gaming research—it’s not a chatbot or emulator.

---

## Requirements

- **Operating System**: macOS or Linux (Windows may require minor tweaks).
- **Python**: Version 3.9 or newer.
- **Python Packages**:
  - `requests`
  - `beautifulsoup4`
  - `rich`
- **Ollama AI**: Installed locally with the `mistral` model.

---

## Installation

Install Python dependencies, fetch the Ollama model, and launch the CLI:

```bash
pip install requests beautifulsoup4 rich
ollama pull mistral
python Darkelf_Retro_CLI.py
```

---

## Usage

Darkelf Retro CLI provides a keyboard-driven, launcher-style interface. Options include:

- Web search
- AI-powered questions
- Retro archives lookup
- Search history review

Simple, number-based selections guide the user through navigation.

---

## License and Ethics

**Darkelf Retro CLI** is intended strictly for educational and research purposes. Users must adhere to:

- Internet Archive terms and conditions.
- VGHF (Video Game History Foundation) guidelines.
- Applicable copyright laws.

---

## Closing

**Darkelf Retro CLI** is crafted for those who appreciate the joy of thumbing through old manuals, uncovering forgotten magazine articles, and delving into the history of why classic games were made the way they were.

Rediscover the golden age of gaming—right from your terminal.
