import sys
import cv2
import numpy as np
import mss
import time
import threading
import pyttsx3
import os
import google.generativeai as genai
from PIL import Image
from PyQt5 import QtWidgets, QtCore

# ================= FASTAPI IMPORTS =================
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# ================= GEMINI CONFIG =================
API_KEY = "YOUR_GEMINI_API_KEY"  # <-- put your Gemini API key here
genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-2.5-flash"

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=(
        "You are an AI assistant for a live video game overlay. "
        "Provide real-time, accurate commentary. Do NOT hallucinate objects not visible."
    ),
)

# ================= SHARED STATE FOR API =================
GLOBAL_STATE = {
    "narration": "",
    "quest": "",
    "villager": "",
    "quest_check": ""
}

# ================= FASTAPI APP =================
api_app = FastAPI()

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_app.get("/state")
def get_state():
    """
    Returns the latest narration, quest, villager line, and quest_check
    produced by the running PyQt overlay app.
    """
    return GLOBAL_STATE


def run_api():
    # Run FastAPI in a background thread
    uvicorn.run(api_app, host="0.0.0.0", port=8000, log_level="info")


# ================= OVERLAY UI (DISABLED FOR ELECTRON INTEGRATION) =================
class OverlayWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setGeometry(40, 40, 1200, 240)
        self.label = QtWidgets.QLabel("Initializing...", self)
        self.label.setStyleSheet(
            "color: white; font-size: 22px; font-weight: bold; "
            "background-color: rgba(0, 0, 0, 170); padding: 10px; border-radius: 10px;"
        )
        self.label.setWordWrap(True)
        self.label.move(20, 20)
        self.label.setFixedWidth(1150)

    def update_text(self, text: str):
        self.label.setText(text)
        self.label.adjustSize()


# ================= GEMINI WORKER =================
class GeminiWorker(QtCore.QThread):
    result_signal = QtCore.pyqtSignal(str)

    def __init__(self, prompt_type: str = "narration"):
        super().__init__()
        self.prompt_type = prompt_type
        self.image_data = None
        self.quest_text = None

    def set_image(self, image, quest_text=None):
        self.image_data = image
        self.quest_text = quest_text

    def run(self):
        if self.image_data is None:
            return
        try:
            resized = cv2.resize(self.image_data, (960, 540), interpolation=cv2.INTER_AREA)
            img_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)

            if self.prompt_type == "narration":
                prompt = "Describe what's happening in this game in 1-2 sentences."
            elif self.prompt_type == "quest":
                prompt = "Create ONE short quest based on this screenshot."
            elif self.prompt_type == "villager":
                prompt = "Say ONE short line as an NPC reacting to this scene"
            elif self.prompt_type == "quest_check":
                if not self.quest_text:
                    self.result_signal.emit("NO - No quest text")
                    return
                prompt = (
                    f"Quest: '{self.quest_text}'. Is it completed? "
                    "Answer 'YES - reason' or 'NO - reason'."
                )
            else:
                prompt = "Describe this scene and just describe if its a gaming interface dont describe anything else"

            response = model.generate_content([prompt, pil_img])
            text = (getattr(response, "text", "") or "").strip()
            if not text:
                text = "No response."
            self.result_signal.emit(text)
        except Exception as e:
            self.result_signal.emit(f"Error: {str(e)}")


# ================= APPLICATION CONTROLLER =================
class AppController:
    def __init__(self):
        # IMPORTANT: Create the QApplication instance
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication(sys.argv)

        # self.overlay = OverlayWindow()
        # self.overlay.show() # Disabled for Electron Frontend integration

        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]

        self.narration_worker = GeminiWorker(prompt_type="narration")
        self.quest_worker = GeminiWorker(prompt_type="quest")
        self.villager_worker = GeminiWorker(prompt_type="villager")
        self.quest_check_worker = GeminiWorker(prompt_type="quest_check")

        self.narration_worker.result_signal.connect(self.on_narration)
        self.quest_worker.result_signal.connect(self.on_new_quest)
        self.villager_worker.result_signal.connect(self.on_villager_line)
        self.quest_check_worker.result_signal.connect(self.on_quest_check_result)

        self.last_narration_text = "Initializing..."
        self.current_quest = None
        self.quest_started_at = time.time()
        self.quest_interval = 5 * 60
        self.quest_check_interval = 15
        self.last_villager_time = 0
        self.villager_cooldown = 30
        self.tts_rate = 170

        self.narration_timer = QtCore.QTimer()
        self.narration_timer.timeout.connect(self.capture_for_narration)
        self.narration_timer.start(5000)

        self.quest_timer = QtCore.QTimer()
        self.quest_timer.timeout.connect(self.maybe_generate_quest)
        self.quest_timer.start(60 * 1000)

        self.check_timer = QtCore.QTimer()
        self.check_timer.timeout.connect(self.check_quest_status)
        self.check_timer.start(self.quest_check_interval * 1000)

        print(f"Game AI Quest System Started with {MODEL_NAME}. Press Ctrl+C to exit.")

    # ---------- TTS ----------
    def speak_text_async(self, text: str):
        def _speak():
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", self.tts_rate)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                print("TTS error:", e)
        threading.Thread(target=_speak, daemon=True).start()

    # ---------- SCREEN CAPTURE ----------
    def grab_frame(self):
        screenshot = np.array(self.sct.grab(self.monitor))
        return screenshot[:, :, :3]

    # ---------- NARRATION ----------
    def capture_for_narration(self):
        if not self.narration_worker.isRunning():
            frame = self.grab_frame()
            self.narration_worker.set_image(frame)
            self.narration_worker.start()

    def on_narration(self, text: str):
        self.last_narration_text = text or "..."
        GLOBAL_STATE["narration"] = self.last_narration_text

        # display = ""
        # if self.current_quest:
        #     display += f"🧭 Quest: {self.current_quest}\n\n"
        # display += f"🎮 {self.last_narration_text}"
        # self.overlay.update_text(display)
        print("Narrator:", text)

    # ---------- QUEST GENERATION ----------
    def maybe_generate_quest(self):
        now = time.time()
        if self.current_quest is None:
            self.start_new_quest()
            return
        if now - self.quest_started_at >= self.quest_interval:
            self.start_new_quest()

    def start_new_quest(self):
        if not self.quest_worker.isRunning():
            frame = self.grab_frame()
            self.quest_worker.set_image(frame)
            self.quest_worker.start()
            self.quest_started_at = time.time()

    def on_new_quest(self, quest_text: str):
        self.current_quest = quest_text or "Unknown quest."
        GLOBAL_STATE["quest"] = self.current_quest

        print("New Quest:", self.current_quest)
        self.speak_text_async(f"New quest: {self.current_quest}")
        # display = f"🧭 Quest: {self.current_quest}\n\n🎮 {self.last_narration_text}"
        # self.overlay.update_text(display)

    # ---------- VILLAGER / NPC ----------
    def trigger_villager_dialogue(self):
        now = time.time()
        if now - self.last_villager_time < self.villager_cooldown:
            return
        if self.villager_worker.isRunning():
            return
        frame = self.grab_frame()
        self.villager_worker.set_image(frame)
        self.villager_worker.start()
        self.last_villager_time = now

    def on_villager_line(self, line: str):
        GLOBAL_STATE["villager"] = line or ""
        print("Villager:", line)
        self.speak_text_async(line)
        # parts = []
        # if self.current_quest:
        #     parts.append(f"🧭 Quest: {self.current_quest}")
        # parts.append(f"🧑‍🌾 Villager: {line}")
        # parts.append(f"🎮 {self.last_narration_text}")
        # self.overlay.update_text("\n\n".join(parts))

    # ---------- QUEST CHECK ----------
    def check_quest_status(self):
        if self.current_quest is None:
            return
        if self.quest_check_worker.isRunning():
            return
        frame = self.grab_frame()
        self.quest_check_worker.set_image(frame, quest_text=self.current_quest)
        self.quest_check_worker.start()

    def on_quest_check_result(self, output: str):
        GLOBAL_STATE["quest_check"] = output or ""
        print("Quest check:", output)
        if isinstance(output, str) and output.strip().lower().startswith("yes"):
            self.speak_text_async("Quest completed! Well done.")
            # self.overlay.update_text(f"✔ Quest Completed!\n\n🎮 {self.last_narration_text}")
            self.current_quest = None
            QtCore.QTimer.singleShot(5000, self.start_new_quest)

    # ---------- MAIN LOOP ----------
    def run(self):
        self.app.exec_()


# ================= MAIN =================
if __name__ == "__main__":
    # Start FastAPI server in background
    threading.Thread(target=run_api, daemon=True).start()

    # Start PyQt overlay app
    controller = AppController()
    controller.run()