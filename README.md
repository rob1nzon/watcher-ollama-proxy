# Watcher → Ollama Proxy

Replaces SenseCAP Watcher Service AI with [Ollama](https://ollama.com).

The physical Watcher device sends images + prompts to the Watcher Service. This proxy intercepts those requests and forwards them to your local Ollama instance instead.

## Quick Start

```bash
pip install -r requirements.txt
python proxy.py
```

## Config

Edit `config.json`:

| Key | Default | Description |
|-----|---------|-------------|
| `port` | `8887` | Port to listen on (same as Watcher Service) |
| `host` | `0.0.0.0` | Bind address |
| `token` | — | Auth token (from Watcher Service config) |
| `ollama_url` | `http://127.0.0.1:11434` | Ollama API endpoint |
| `model` | `gemma3:latest` | Ollama model to use (must support vision for images) |
| `temperature` | `0.3` | LLM temperature |
| `timeout` | `120` | Ollama request timeout (seconds) |

You can also update config at runtime:

```bash
curl -X POST http://localhost:8887/config -H 'Content-Type: application/json' -d '{"model":"llava"}'
```

## API

### `POST /v1/watcher/vision`

Main endpoint — called by Watcher device.

```json
{
  "img": "<base64 JPEG>",
  "prompt": "if you see a cat, say hi",
  "audio_txt": "",
  "type": 1
}
```

Response:

```json
{
  "code": 200,
  "msg": "",
  "data": {
    "state": 1,
    "audio": "",
    "img": "",
    "res": "<LLM response>"
  }
}
```

### `GET /health`

Health check.

### `GET/POST /config`

View or update config at runtime.

## Setup

1. Stop Watcher Service (if running)
2. Make sure [Ollama](https://ollama.com) is running with a vision-capable model:
   ```bash
   ollama pull gemma3
   ```
3. Start the proxy:
   ```bash
   python proxy.py
   ```
4. Point your Watcher device to this machine's IP on port 8887

## Compatible Models

For image analysis, use a vision-capable model:

- `gemma3` — good balance of quality and speed
- `llava` — popular vision model
- `minicpm-v` — lightweight option

Text-only models work too, but won't process images from the Watcher device.
