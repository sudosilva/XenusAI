"""
XenusAI — Eel GUI Application
Launches the ChatGPT-style web interface as a desktop app.

Usage:
    python app.py
"""

import sys
import os
import logging
import threading
import traceback
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import speech_recognition as sr
import tempfile
from typing import List, Dict

# ─── Ensure project root is on sys.path ────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import eel

# ─── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("XenusAI")

# ─── Initialize Eel ───────────────────────────────────────────
WEB_DIR = os.path.join(PROJECT_ROOT, "interface", "web")
eel.init(WEB_DIR)

# ─── Exposed Functions ────────────────────────────────────────


@eel.expose
def py_search(query, history=None, n_results=5):
    """Handle a user query (conversational or knowledge search)."""
    try:
        from retrieval.llm import generate_response
        response = generate_response(query, history=history, n_results=n_results)
        return response
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "type": "error",
            "message": f"An error occurred: {str(e)}",
            "results": []
        }


@eel.expose
def py_ingest(source):
    """Ingest a URL, file, or directory into the knowledge base."""
    try:
        from pipelines.ingest import ingest
        result = ingest(source, verbose=False)
        return result
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        return {"status": "error", "message": str(e)}


@eel.expose
def py_get_stats():
    """Get knowledge base statistics."""
    try:
        from pipelines.embedder import get_stats
        stats = get_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "total_chunks": 0,
            "unique_sources": 0,
            "sources": [],
            "collection_name": "unknown",
        }


@eel.expose
def py_delete_source(source):
    """Delete all chunks from a specific source."""
    try:
        from pipelines.embedder import delete_source
        count = delete_source(source)
        return {"status": "success", "deleted": count}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return {"status": "error", "message": str(e)}


@eel.expose
def py_reset():
    """Reset the entire knowledge base."""
    try:
        from pipelines.embedder import reset_collection
        reset_collection()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Reset error: {e}")
        return {"status": "error", "message": str(e)}


# ─── Seamless Python OS-Native STT Routines ──────────────────
is_recording = False
recorded_frames = []
audio_stream = None

@eel.expose
def py_get_microphones():
    """Retrieve a list of all physical input devices from the OS hardware registry."""
    try:
        devices = sd.query_devices()
        default_idx = sd.default.device[0]
        mics = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                mics.append({"id": i, "name": dev['name']})
        return {"status": "success", "mics": mics, "default": default_idx}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@eel.expose
def py_start_dictation(device_id=None):
    """Start listening to a specific microphone stream natively."""
    global is_recording, recorded_frames, audio_stream
    is_recording = True
    recorded_frames = []
    
    def callback(indata, frames, time, status):
        if is_recording:
            recorded_frames.append(indata.copy())
            
    # Force 16-bit PCM integer instead of Float32 so the Python wave parser doesn't crash
    if device_id is not None:
        try:
            device_id = int(device_id)
        except ValueError:
            device_id = None
            
    audio_stream = sd.InputStream(
        samplerate=44100, 
        channels=1, 
        dtype='int16', 
        device=device_id, 
        callback=callback
    )
    audio_stream.start()
    return True

@eel.expose
def py_stop_dictation():
    """Terminate stream, collapse frames to WAV buffer, and process text."""
    global is_recording, recorded_frames, audio_stream
    is_recording = False
    
    if audio_stream:
        audio_stream.stop()
        audio_stream.close()
        
    if not recorded_frames:
        return {"status": "error", "message": "No audio captured from hardware."}
        
    try:
        # Collapse the recorded audio lists into a continuous tensor stream
        recording = np.concatenate(recorded_frames, axis=0)
        
        # Hardcheck physical microphone levels out of 32,768 (16-bit PCM cap)
        max_amp = np.max(np.abs(recording))
        if max_amp < 1500:
            return {"status": "error", "message": "Voice not detected. Please speak louder into the microphone!"}
            
        temp_dir = tempfile.gettempdir()
        temp_wav = os.path.join(temp_dir, "xenus_dictation.wav")
        wav.write(temp_wav, 44100, recording)
        
        # Ping Google Transcriber locally from Python
        r = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            
            # Filter standard Google API Neural Hallucinations generated by physical room static
            ghosts = ["you", "thank you.", "thank you", "thanks.", "subscribe", "thanks for watching."]
            if text.strip().lower() in ghosts:
                return {"status": "error", "message": "Neural noise blocked. Please repeat."}
                
            return {"status": "success", "text": text}
            
    except sr.UnknownValueError:
        return {"status": "error", "message": "Voice was too faint or unintelligible."}
    except sr.RequestError as e:
        return {"status": "error", "message": f"Recognizer offline block: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ─── Launch ───────────────────────────────────────────────────

def main():
    """Launch XenusAI GUI."""
    logger.info("Starting XenusAI...")
    logger.info(f"Web directory: {WEB_DIR}")

    try:
        import webbrowser
        try:
            webbrowser.open("http://localhost:8147/index.html")
            logger.info("Opening UI in system default browser...")
        except Exception as e:
            logger.warning(f"Could not open browser automatically: {e}")
            logger.info("Please open http://localhost:8147 in your browser manually.")
            
        # Launching with mode=None ensures Eel sets up the WebSocket and waits infinitely,
        # preventing the script from crashing even if it can't find a browser executable.
        eel.start(
            "index.html",
            size=(1280, 820),
            position=(100, 50),
            port=8147,
            mode=None,
        )
    except Exception as e:
        logger.error(f"Eel host server crashed: {e}")


if __name__ == "__main__":
    main()
