#!/usr/bin/env python3
"""Watcher → Ollama proxy: replaces SenseCAP Watcher Service with Ollama."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import requests
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("watcher-proxy")

app = Flask(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULT_CONFIG = {
    "port": 8887,
    "host": "0.0.0.0",
    "token": "f3sp996d5rxu",
    "ollama_url": "http://127.0.0.1:11434",
    "model": "gemma3:latest",
    "temperature": 0.3,
    "timeout": 120,
}


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        # merge defaults
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


CFG = load_config()

# ── Helpers ─────────────────────────────────────────────────────────────────


def call_ollama(prompt: str, image_b64: str | None = None) -> str:
    """Send a request to Ollama API."""
    payload = {
        "model": CFG["model"],
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": CFG["temperature"]},
    }
    if image_b64:
        payload["images"] = [image_b64]

    resp = requests.post(
        f"{CFG['ollama_url']}/api/generate",
        json=payload,
        timeout=CFG["timeout"],
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "")


def make_response(state: int = 1, res: str = "", audio: str = "", img: str = ""):
    return jsonify({"code": 200, "msg": "", "data": {"state": state, "audio": audio, "img": img, "res": res}})


# ── Routes ──────────────────────────────────────────────────────────────────


@app.route("/v1/watcher/vision", methods=["POST", "OPTIONS"])
def vision():
    if request.method == "OPTIONS":
        return "", 200

    # Auth
    token = request.headers.get("Authorization", "")
    if token != CFG["token"]:
        log.warning("Reject: bad token %r", token)
        return jsonify({"code": 401, "msg": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    prompt = body.get("prompt", "")
    img = body.get("img", "")
    audio_txt = body.get("audio_txt", "")
    req_type = body.get("type", 0)

    log.info("Vision request: prompt=%r  has_img=%s  audio=%r  type=%s", prompt, bool(img), audio_txt, req_type)

    if not prompt and not img:
        return make_response(state=0)

    try:
        result = call_ollama(prompt or "Describe what you see", img or None)
        log.info("Ollama response: %s", result[:200])
        return make_response(state=1, res=result)
    except Exception as e:
        log.error("Ollama error: %s", e)
        return make_response(state=0, res=str(e))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": CFG["model"], "ollama": CFG["ollama_url"]})


@app.route("/config", methods=["GET"])
def get_config():
    return jsonify(CFG)


@app.route("/config", methods=["POST"])
def update_config():
    global CFG
    body = request.get_json(silent=True) or {}
    for k, v in body.items():
        if k in DEFAULT_CONFIG:
            CFG[k] = v
    save_config(CFG)
    return jsonify({"ok": True, "config": CFG})


# catch-all
@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "OPTIONS"])
def fallback(path):
    if request.method == "OPTIONS":
        return "", 200
    return jsonify({"code": 200, "msg": "OK", "data": {}})


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    log.info("🚀 Watcher→Ollama proxy")
    log.info("   Port: %s", CFG["port"])
    log.info("   Token: %s", CFG["token"])
    log.info("   Ollama: %s", CFG["ollama_url"])
    log.info("   Model: %s", CFG["model"])
    app.run(host=CFG["host"], port=CFG["port"])
