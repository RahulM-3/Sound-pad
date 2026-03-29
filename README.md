# Soundpad
<div align="left">Authored by: <b><a href="https://github.com/RahulM-3">Rahul</a></b></div>

A modern, desktop soundboard application built with Python and PyQt6. Route audio clips directly to your virtual microphone (e.g., VB-Audio CABLE) with ease via a sleek, dark-themed glassmorphic user interface.

## Features

- **Profile Management**: Group sounds into profiles (e.g., Memes, Music, SFX). Profiles are literally just folders inside the `audio/` directory. You can bulk upload via the app or simply drag-and-drop `.wav` files directly into those Windows folders!
- **Virtual Mic Auto-Switch**: Automatically detects "CABLE Output" in your Windows recording devices, sets it as your default microphone while the app is open, and restores your original microphone on close.
- **Microphone Fail-Safe**: Even if the app crashes or is force-killed via Task Manager, it uses a persistent memory cache to remember your *real* microphone. Your recording devices are always kept perfectly safe.
- **Audio Trimming**: Visually crop and trim audio files directly in the app before adding them.
- **Universal Format Support**: Supports MP3, OGG, FLAC, M4A, WAV, and more.

## Requirements

### Hardware / Software
1. **Windows OS**: Recommended for native audio routing.
2. **VB-Audio Virtual Cable**: [Download here](https://vb-audio.com/Cable/). This routes the soundboard playback output directly into your system microphone input.
3. **PowerShell AudioDeviceCmdlets**: The app uses this module to smoothly background-switch your microphone.
   - *Install via PowerShell (Admin):* `Install-Module -Name AudioDeviceCmdlets -Force`
4. **FFmpeg**: Required only for MP3/M4A support. Ensure `ffmpeg` is in your system PATH.

### Python Dependencies
Using Python 3.10+, simply install via:
```powershell
pip install -r requirements.txt
```

## Running the Application

Ensure your terminal is inside the project directory and your virtual environment is active:
```powershell
python app.py
```

## Compiling to EXE

We've included an automated script to immediately compile the entire application into a standalone Windows `.exe` file wrapped with a native, high-quality icon!

1. Open your terminal in the project directory.
2. Run the provided compile script:
   ```powershell
   .\compile.bat
   ```

Your finished executable will be waiting inside the freshly created `dist/` folder named **`Soundpad.exe`**!