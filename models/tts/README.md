# Piper TTS Voice Models

Place Piper TTS voice models (`.onnx` + `.onnx.json`) in this folder.

Piper will auto-discover models placed here.

## Download

List available voices:

```bash
python -m piper.download_voices
```

Download a specific voice:

```bash
python -m piper.download_voices en_US-lessac-medium --data-dir models/tts
```

Or download manually from the [Piper voice repository](https://huggingface.co/rhasspy/piper-voices) and place both the `.onnx` and `.onnx.json` files here.

## Usage

Set `PIPER_MODEL` env var to use a specific model path:

```bash
export PIPER_MODEL=/path/to/voice.onnx
```
