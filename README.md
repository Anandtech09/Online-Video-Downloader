# StreamFlow - Universal Online Media Downloader ⚡

A high-performance, mobile-friendly media downloader web application built with **Python Streamlit**. Download videos, music, and photos from YouTube, Instagram, TikTok, Facebook, Twitter/X, Reddit, Vimeo, SoundCloud, and direct media URLs directly into your phone or laptop.

---

## 🌟 Key Features

### 1. 📱 Direct Device Downloads (Mobile & Laptop)
- Downloads trigger the client browser's native file transfer and save directly into your **device's default `Downloads` folder** (Android internal storage, iOS Files, or Windows/macOS Downloads).
- Zero server clutter: Temporary server-side files are automatically purged so the deployment instance storage is never consumed.

### 2. 🛡️ Pre-Download Security Audit Scanner
- Automatically scans every link before downloading starts.
- **SSRF & Private Network Protection:** Blocks access to `localhost`, `127.0.0.1`, cloud metadata IP (`169.254.169.254`), and internal network ranges.
- **Malware Prevention:** Blocks dangerous executable extensions (`.exe`, `.bat`, `.cmd`, `.sh`, `.ps1`, `.msi`, `.vbs`, etc.).
- Verifies secure HTTPS encryption and media stream signatures.

### 3. ✂️ 15-Character Filename Truncation Policy
- Slices large video titles so the base name is strictly **max 15 characters** (e.g., `Super Long Title Video 2026.mp4` &rarr; `Super Long Titl.mp4`), keeping your file system clean while preserving the original video title in the UI.

### 4. 🎛️ Automatic Video Quality Detection
- Analyzes stream availability and presents quality choices:
  - `2160p (4K UHD)`
  - `1440p (2K QHD)`
  - `1080p (Full HD)`
  - `720p (HD)`
  - `480p (SD)`
  - `Audio Only (MP3 320kbps)`
- **Direct Stream Bypass:** If a link only has a single quality or is a direct media stream, it bypasses unnecessary dropdowns and offers direct 1-click download.

### 5. 🚀 500MB+ Large File Resilience
- Tuned for large files (500MB - 2GB+) with:
  - 4MB socket I/O buffer
  - 10MB chunked HTTP streaming
  - 20 fragment retries with zero fragment skipping (guarantees zero missing data)
  - Lossless FFmpeg audio/video stream muxing at original source bitrates

### 6. ⚡ Batch Downloader (10+ URLs at once) with 3x Retry & Master ZIP
- Paste 10, 20, or more links at once.
- Downloads concurrently using background worker threads.
- **3-Attempt Automated Retry:** Automatically recovers from network glitches or transient errors. If still failed after 3 tries, lists under Failed with the reason.
- **1-Click Master ZIP Archive:** Bundles all successfully downloaded files into a single ZIP file for one-tap saving to your device.

---

## 📂 Project Architecture

```text
├── app.py                      # Main Streamlit web application & UI
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation & Deployment guide
├── .streamlit/
│   └── config.toml             # Streamlit dark theme & 1GB static streaming config
├── core/                       # Modularized Core Logic Package
│   ├── __init__.py             # Core package export interface
│   ├── downloader.py           # Universal media download engine
│   ├── security.py             # Pre-download security audit (SSRF & malware blocker)
│   ├── utils.py                # 15-char title sanitizer, byte format & folder mover
│   └── styles.py               # Modern responsive mobile & desktop CSS
└── static/
    └── downloads/              # Organized Download Directory
        ├── large_files/        # Dedicated folder for 500MB+ / 100MB+ big files
        ├── videos/             # Standard video streams
        ├── audio/              # MP3 / HQ audio files
        ├── photos/             # Photos & images
        └── batch/              # 1-Click Master ZIP bundles
```

---

## 🚀 Running Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Application
```bash
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## ☁️ Deploying to Streamlit Cloud

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository, set Main file path to `app.py`, and click **Deploy**!
4. The application is immediately live on the web with mobile and desktop support.
