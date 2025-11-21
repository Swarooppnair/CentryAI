# 🎮 AI-Powered Minecraft Overlay (Real-Time Narration + Quests + NPC Dialogue)

This project adds an **AI-powered HUD overlay** on top of Minecraft (or any game).  
It uses **Gemini 2.5 Flash**, **screen capture**, **FastAPI**, and an **Electron transparent overlay** to display:

✔ Real-time narration  
✔ AI-generated quests  
✔ NPC villager reactions  
✔ Automatic quest completion detection  
✔ Live updates inside a unified HUD box  

All powered using a **zero-click-through transparent Electron overlay**.

---





## 🚀 Features

### 🔹 Real-Time Narration  
The system analyzes the game screen every few seconds and describes the scene in **1–2 sentences**.

### 🔹 Dynamic Quests  
Every few minutes, the AI generates a new short quest based on the current gameplay.

### 🔹 NPC / Villager Reactions  
Random NPC-style one-liners reacting to what is happening in the game.

### 🔹 Quest Completion Check  
AI compares the **current screenshot** with the **current quest** and returns:  
`YES – reason` or `NO – reason`.

### 🔹 Electron HUD Overlay  
Displays everything in a single Minecraft-style UI box on the **top-left** of the screen.

### 🔹 Click-Through Window  
The overlay is **fully transparent** and does not block any mouse input in the game.

---

## 🏗 Architecture Overview

┌─────────────────────┐
│ Video Game │
│ (Minecraft / etc) │
└─────────┬───────────┘
│ Screen Capture (mss)
▼
┌─────────────────────┐
│ Python AI │
│ - Gemini 2.5 Flash │
│ - Quest System │
│ - Narration │
│ - NPC Dialogue │
└─────────┬───────────┘
│ Exposes API (/state)
▼
┌─────────────────────┐
│ FastAPI Server │
└─────────┬───────────┘
│ Fetch state JSON (every 2 sec)
▼
┌─────────────────────┐
│ Electron Overlay │
│ (Transparent HUD) │
└─────────────────────┘


---

## 📦 Requirements

### Python Dependencies

Python 3.10+
PyQt5
FastAPI
Uvicorn
opencv-python
numpy
mss
Pillow
pyttsx3
google-generativeai

Node.js 18+
Electron 28+

npm install

Open app.py and set your Gemini key:

API_KEY = "YOUR_API_KEY_HERE"

2️⃣ Start the Python Backend (AI Engine)

Run:

python app.py


This will:

Start the FastAPI server on http://localhost:8000/state

Start screen capture

Start narration / quest generation

Continuously update GLOBAL_STATE

3️⃣ Run the Electron Transparent Overlay
npm start


Electron will open a full screen invisible window showing the HUD.

✔ Always on top
✔ Transparent
✔ Click-through

📁 Project Structure
/project-root
│
├── app.py               # Python AI + FastAPI backend
├── index.html            # Electron overlay UI
├── main.js               # Electron config (transparent window)
├── package.json          # Electron app config
└── README.md             # Documentation

🌐 API Endpoint
GET /state

Returns:

{
  "narration": "Player is exploring the woods...",
  "quest": "Find a hidden cave nearby.",
  "villager": "Oi traveler, keep your torch ready!",
  "quest_check": "NO - cave not discovered yet"
}

🧠 Future Improvements

NPC personality system

Per-biome quest generator

Custom mod data feed from Minecraft

Multiplayer team-based quests

Voice-controlled interaction



-----------------------------------DATABASE-------------------------------------------------------------


# Game AI with MongoDB Vector Database

A game AI overlay system with MongoDB vector database storage and FastAPI backend.

## Features

- Real-time game narration using Gemini AI
- Quest generation and tracking
- NPC dialogue system
- MongoDB storage with vector embeddings for semantic search
- FastAPI REST API endpoints
- Vector similarity search for context retrieval

## Setup

1. Install MongoDB:
bash
brew install mongodb-community
brew services start mongodb-community


2. Install Python dependencies:
bash
pip install -r requirements.txt


3. Configure environment:
bash
cp .env.example .env
# Edit .env with your settings


## Running

1. Start the API server:
bash
python api_server.py


2. In another terminal, run the game overlay:
bash
python main_integrated.py


## API Endpoints

- POST /chat - Store chat messages
- POST /context - Store context data
- POST /quest - Store quests
- POST /search - Semantic search
- GET /chats/recent - Get recent chats
- GET /quests/active - Get active quests
- PUT /quest/status - Update quest status

## Example API Usage

python
import requests

# Store a chat
requests.post("http://localhost:8000/chat", json={
    "chat_type": "narration",
    "text": "The player is exploring a dark forest",
    "metadata": {"location": "forest"}
})

# Semantic search
requests.post("http://localhost:8000/search", json={
    "query": "forest exploration",
    "collection": "chats",
    "limit": 5
})


-------------------------------------------------------------------FINE TUNNED MODEL---------------------------------------------------------------------------------------------------------

Repo link: Bharathparam11/The_Reverse_Wisperer_TTS


