# Ollama Setup Guide for Darkelf Retro AI

This guide explains how to install, set up, and update **Ollama** using Homebrew, ensuring it's ready for use with Darkelf Retro AI.

---

## **1. Install Ollama via Homebrew**

### Step 1: Update Homebrew
Before installing Ollama, ensure Homebrew is up-to-date:
```bash
brew update
```

### Step 2: Install Ollama
Use Homebrew to install Ollama:
```bash
brew install ollama
```

### Step 3: Verify Installation
Check if Ollama was installed successfully by confirming its version:
```bash
ollama version
```
You should see a version number (e.g., `0.11.6`).

---

## **2. Start the Ollama Server**

Ollama requires its local server to be running to process AI queries.

### Start the Server Manually
You can start the server manually with:
```bash
ollama start
```

### Start the Server as a Background Service
To run Ollama as a system service that starts with your computer:
```bash
brew services start ollama
```

### Restart or Stop the Server
If needed, restart or stop the server:
```bash
brew services restart ollama  # Restart
brew services stop ollama     # Stop
```

### Check the Server Status
Confirm whether the Ollama server is running as a service:
```bash
brew services list
```
In the list, locate **ollama**, which should show the status as `started`.

---

## **3. Download the AI Model**

Once the server is running, download the required **llama3** model:
```bash
ollama pull llama3
```
This command downloads the model so it’s ready for use in Darkelf Retro AI.

---

## **4. Update Ollama**

To keep Ollama up-to-date, perform the following steps:

### Step 1: Update Homebrew
Refresh the Homebrew formula list:
```bash
brew update
```

### Step 2: Upgrade Ollama
Upgrade to the latest version of Ollama:
```bash
brew upgrade ollama
```

### Step 3: Verify the Update
Check the version to ensure you're running the latest one:
```bash
ollama version
```

---

## **5. Troubleshooting Common Issues**

### Ollama Server Not Responding
- Ensure the server is running:
  ```bash
  ollama start
  ```
- Restart the server if it's unresponsive:
  ```bash
  brew services restart ollama
  ```
- Confirm the server is listening on `127.0.0.1:11434` by visiting:
  [http://127.0.0.1:11434](http://127.0.0.1:11434)

### Ollama Command Not Found
- Ensure Ollama is installed and on your system's PATH:
  ```bash
  brew link --overwrite ollama
  ```

### Insufficient Permissions on `OLLAMA_MODELS`
- Resolving permission issues for the directory:
  ```bash
  mkdir -p /Users/kevinmoore/.ollama/models
  chmod +rw /Users/kevinmoore/.ollama/models
  ```

---

## **6. Common Commands Recap**

| **Task**                | **Command**                          |
|-------------------------|--------------------------------------|
| Update Homebrew         | `brew update`                       |
| Install Ollama          | `brew install ollama`               |
| Start Ollama Server     | `ollama start`                      |
| Start as Service        | `brew services start ollama`        |
| Restart Ollama Server   | `brew services restart ollama`      |
| Stop Ollama Server      | `brew services stop ollama`         |
| Upgrade Ollama          | `brew upgrade ollama`               |
| Verify Installation     | `ollama version`                    |
| Check Running Services  | `brew services list`                |
| Download `llama3` Model | `ollama pull llama3`                |

---

## **7. Example Workflow**

Here’s an example of setting up Ollama for Darkelf Retro AI:

1. Update Homebrew:
   ```bash
   brew update
   ```

2. Install Ollama:
   ```bash
   brew install ollama
   ```

3. Start the Server:
   ```bash
   ollama start
   ```

4. Download the `llama3` Model:
   ```bash
   ollama pull llama3
   ```

5. Use Ollama in Darkelf Retro AI:
   - Run your Python script.
   - Select **Option 2 (Ask Darkelf OSINT AI)** or **Option 5 (OSINT Challenges)**.
   - Interact with the AI seamlessly.

---

## **8. Uninstall Ollama (If Needed)**
To fully remove Ollama, use:
```bash
brew uninstall ollama
```

---

By following these instructions, Ollama should now work seamlessly with Darkelf Retro AI. If you encounter any issues, refer back to the troubleshooting section or contact support.
