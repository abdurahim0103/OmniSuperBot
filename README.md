# ⚡ Omni Super — Universal All-in-One Media & AI Platform

[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-emerald.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.22-sky.svg)](https://docs.aiogram.dev/)
[![Security Hardened](https://img.shields.io/badge/Security-SSRF%20Guarded%20%26%20Vaulted-purple.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-gray.svg)](#)

**Omni Super** is a single, unified, high-performance multimedia and AI platform engineered for both the Web and Telegram. It provides 6 high-reliability core features with zero paid API dependencies, 10-language global localization (i18n), and robust cybersecurity hardening.

---

## 🌟 6 Core Features

1. **📂 Lossless File Converter**
   - High-fidelity format conversion: Excel (`.xlsx`, `.xls`), `.csv`, Word (`.docx`, `.doc`), `.pdf`, `.html`, `.json`, `.txt`, and images (`.jpg`, `.png`, `.webp`).
   - 1:1 table structure and layout integrity preservation.
   - Batch conversion with instant ZIP package download.

2. **🎬 Universal Video & Audio (MP3) Downloader**
   - Direct watermark-free HD video download from TikTok, Instagram, YouTube, and direct media URLs.
   - Studio-grade audio extraction in MP3 and lossless WAV formats.
   - Integrated SSRF protection against internal/loopback network targets.

3. **🌍 Professional AI Translator (Top 10 Languages)**
   - 100% reliable translation across 10 major world languages:
     - 🇺🇿 Uzbek, 🇬🇧 English, 🇷🇺 Russian, 🇹🇷 Turkish, 🇸🇦 Arabic, 🇨🇳 Chinese, 🇪🇸 Spanish, 🇩🇪 German, 🇫🇷 French, 🇰🇷 Korean.
   - Multi-tier fallback architecture: Primary Google AT Engine ➔ English Pivot Routing ➔ MyMemory NMT.
   - In-image visual subtitle rendering and Web Speech API text-to-speech.

4. **✨ 3D Pixar Cartoon Transformation**
   - Client-side & server-side photo animators.
   - 2-pass surface smoothing (porcelain skin), saturation boost (+42%), contrast enhancement, subsurface scattering bloom, and crisp cartoon unsharp masking.
   - 4K PNG export and 3D mesh (.OBJ) generation.

5. **🔮 AI Magic Studio (Idea 1)**
   - 1-click intelligent background removal (Transparent, Neon Studio, Dark Studio, Pure White).
   - 4K Ultra-HD super-resolution upscale and micro-contrast sharpener.

6. **🎧 Cyberpunk Audio Studio & Visualizer (Idea 2)**
   - 60 FPS real-time Web Audio API dynamic spectrum visualizer.
   - Out-of-Phase Stereo (OOPS) vocal and karaoke/instrument isolation.
   - Interactive synthesizer and custom audio waveform generator.

---

## 🛡️ Cybersecurity & Hardened Secrets

- **Zero Cleartext Credentials:** Tokens and secrets are consolidated in a root `.env` file that is strictly ignored by Git (`.gitignore`).
- **Web Server Protection:** `netlify.toml` and server rules reject any HTTP/HTTPS requests targeting `.env*` or `.git*` with `403 Forbidden`.
- **SSRF Defense:** URL parser strictly validates hostnames and IP addresses, blocking `localhost`, `127.0.0.1`, RFC1918 private CIDR blocks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and AWS/GCP cloud metadata endpoints (`169.254.169.254`).
- **DoS / Memory Guard:** Memory-safe downscaling on client and server to prevent resource exhaustion attacks.

---

## 🚀 Quick Start (Local Development)

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/<YOUR_USERNAME>/OmniSuperBot.git
cd OmniSuperBot

# Copy environment configuration template
cp .env.example .env

# Edit .env and insert your Telegram Bot Token
nano .env
```

### 2. Run Telegram Bot
```bash
cd omnibot
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt
python bot.py
```

### 3. Run Web Interface
```bash
# In the root directory:
python3 -m http.server 8000
# Open http://localhost:8000 in your browser
```

---

## ☁️ 24/7 Cloud Deployment

### Option A: Docker (Recommended)
```bash
docker build -t omni-super-platform .
docker run -d --name omni-super --env-file .env --restart always omni-super-platform
```

### Option B: Render.com
1. Create a new Web/Worker service on [Render.com](https://render.com).
2. Connect your GitHub repository `OmniSuperBot`.
3. Render will automatically detect `render.yaml`.
4. Add your `BOT_TOKEN` in the Environment Variables dashboard.

### Option C: Railway.app
1. Deploy from GitHub repository.
2. Add environment variable `BOT_TOKEN`.
3. Deploy!

---

## 🌐 Global Localization (i18n)

The web frontend includes a global language switcher that dynamically re-renders all UI text without page reloads. The selected preference is automatically persisted to `localStorage`.

---

## 📄 License
MIT License. Free for personal and commercial usage.
