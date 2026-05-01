# 🔧 Forensic Report Analyzer — Problems & Solutions Sheet

> This document lists every major problem we faced during the development of the Forensic Report Analyzer project and how each was solved.

---

## 📋 Project Overview

**Project:** AI-powered Forensic Report Analyzer  
**Purpose:** Detect tampering in official postmortem/forensic reports by cross-verifying them against on-the-spot body condition observations  
**Tech Stack:** Python, Flask, SQLite, spaCy, Tesseract OCR, OpenCV, Three.js  
**GitHub:** https://github.com/RajGautam8113/forensic-report-analyzer  

---

## Problem #1: Basic 2D UI — Not Professional Looking

| | Details |
|---|---|
| **Problem** | The original website had a plain, basic 2D interface with no animations or premium feel. It looked like a simple college project. |
| **Impact** | Poor first impression, didn't convey the seriousness of the tool. |
| **Solution** | Complete 3D redesign using **Three.js** (loaded via CDN) with: |
| | • 2,500+ floating particle nebula background |
| | • Rotating DNA double helix animation |
| | • 6 orbiting glowing spheres with mouse-reactive parallax |
| | • Glassmorphism UI (frosted glass cards with neon borders) |
| | • Holographic upload zone with scanning beam animations |
| | • Premium dark theme with cyan/purple color palette |
| **Files Changed** | `static/css/theme.css` (NEW), `static/js/three-scene.js` (NEW), all 4 HTML templates redesigned |
| **Lesson** | First impression matters — a professional UI builds trust. |

---

## Problem #2: No File Validation — Accepted ANY File

| | Details |
|---|---|
| **Problem** | The original `is_postmortem_report()` function used simple keyword matching (like "examination", "report"). A **resume** or any random PDF with common words was accepted as a valid forensic report. |
| **Impact** | Garbage in = garbage out. Non-medical files produced meaningless results, wasting time and giving false analysis. |
| **Solution** | Replaced with a **5-layer scoring system**: |
| | **Layer 1:** Mandatory medical keywords check (autopsy, postmortem, cause of death, etc.) |
| | **Layer 2:** Medical terminology density scoring (rigor mortis, toxicology, laceration, etc.) |
| | **Layer 3:** Anti-pattern detection — reject if resume/invoice/legal terms found |
| | **Layer 4:** Structural pattern matching (section headers like "External Examination", "Internal Organs") |
| | **Layer 5:** Minimum score threshold (score < 40 = rejected) |
| **Files Changed** | `main.py` — rewrote `is_postmortem_report()` function |
| **Lesson** | Input validation is the first line of defense against bad data. |

---

## Problem #3: No Body Condition Input — Report Analyzed in Isolation

| | Details |
|---|---|
| **Problem** | The system only read the uploaded report and extracted text from it. There was **no way to input what was actually observed on the victim's body** at the spot. Without comparison data, the system couldn't detect if the report was tampered. |
| **Impact** | The whole purpose — detecting tampering — was impossible without comparison data. |
| **Solution** | Added a **multi-step form** (3 steps): |
| | **Step 1:** Upload forensic report (PDF/TXT/DOCX/Image) |
| | **Step 2:** Enter on-the-spot body conditions — dynamic injury entries with type (fracture, laceration, bruise, etc.), body part, severity (mild/moderate/severe/fatal), bleeding (yes/no), and description |
| | **Step 3:** Review everything before submitting |
| **Files Changed** | `index.html` (complete redesign), `main.py` (form parsing), `models.py` (body_conditions table) |
| **Lesson** | Cross-verification needs two data sources to compare. |

---

## Problem #4: No Cross-Verification Engine

| | Details |
|---|---|
| **Problem** | The system had no logic to **compare** the report data against body conditions. It just displayed extracted text. |
| **Impact** | No tampering detection, no consistency scoring, no AI verdict. |
| **Solution** | Built three new engines: |
| | **1. Injury Analyzer** (`injury_analyzer.py`) — Rule-based medical logic mapping 20+ injury types to probable causes of death, with severity scoring and assault vs accident indicators |
| | **2. Cross-Verifier** (`cross_verifier.py`) — Compares report findings vs body conditions, calculates consistency score (0-100%), assigns tampering risk level (LOW/MEDIUM/HIGH/CRITICAL), identifies red flags |
| | **3. AI Verdict** — Independent cause-of-death determination based purely on body evidence, separate from what the report says |
| **Files Changed** | `injury_analyzer.py` (NEW), `cross_verifier.py` (NEW), `nlp_utils.py` (enhanced), `models.py` (verification tables) |
| **Lesson** | An analysis tool without an analysis engine is just a file viewer. |

---

## Problem #5: No Evidence Media Upload (Images/Videos)

| | Details |
|---|---|
| **Problem** | Users couldn't upload **photos or videos** of the victim's body condition. Text-only injury input missed visual evidence that could be critical for detection. |
| **Impact** | Important visual evidence (photos of injuries, videos of crime scene) couldn't be used for analysis. |
| **Solution** | Added **evidence media upload** with: |
| | • Drag-and-drop upload zone in Step 2 (supports JPG, PNG, MP4, AVI, etc.) |
| | • Client-side preview thumbnails for images, video poster frames |
| | • File removal with ✕ button |
| | • Max 10 files limit |
| | • Backend processes images with **OCR** to extract text |
| | • Backend processes videos by extracting **keyframes** (every 2 seconds) and running OCR on each |
| | • Extracted text feeds into cross-verifier for enhanced analysis |
| **Files Changed** | `media_processor.py` (NEW), `index.html`, `result.html` (evidence gallery tab), `report_detail.html` (evidence section), `main.py`, `models.py` (evidence_media table) |
| **Lesson** | Visual evidence is as important as textual evidence in forensics. |

---

## Problem #6: Evidence Gallery Not Showing in Results

| | Details |
|---|---|
| **Problem** | Backend processed and stored evidence media, but the **result page and report detail page** had no UI to display the uploaded images/videos and their OCR-extracted text. |
| **Impact** | Users couldn't see their uploaded evidence or the OCR text extracted from it. |
| **Solution** | Added to both `result.html` and `report_detail.html`: |
| | • **"📸 Evidence Media"** tab with responsive gallery grid |
| | • Image thumbnails with **lightbox zoom** (click to fullscreen) |
| | • Embedded **video players** with controls |
| | • OCR text display below each media item |
| | • Type badges (Image/Video) |
| | • "No text detected" fallback message |
| **Files Changed** | `result.html`, `report_detail.html` |
| **Lesson** | Every feature needs both backend processing AND frontend display. |

---

## Problem #7: ngrok Command Not Working

| | Details |
|---|---|
| **Problem** | User ran `ngrok https 8080` but it silently exited with no output. |
| **Root Cause** | Two issues: |
| | 1. Wrong command — should be `ngrok http` (not https), Flask runs on HTTP |
| | 2. The `ngrok` command resolved to an **npm wrapper package** (`C:\Users\rg620\AppData\Roaming\npm\ngrok.ps1`) instead of the actual ngrok CLI |
| **Solution** | Installed the real ngrok CLI via `winget install ngrok.ngrok`, then used the correct command: `ngrok http 8080` |
| **Lesson** | Always check `where <command>` or `Get-Command` to verify which binary is being executed. npm packages can shadow system binaries. |

---

## Problem #8: Deployment Failed — EasyOCR + PyTorch Too Heavy (2.5GB)

| | Details |
|---|---|
| **Problem** | Project used **EasyOCR** which depends on **PyTorch (~2GB)** + torchvision. Free tier platforms (Render, Railway) have limited memory (512MB RAM, limited build resources). Docker build kept running out of memory or exceeding size limits. |
| **Impact** | Project couldn't be deployed anywhere for free. System off = project offline. |
| **Solution** | **Replaced EasyOCR with Tesseract OCR**: |
| | • Removed: `easyocr`, `torch` (2GB), `torchvision` (500MB) |
| | • Added: `pytesseract` (50KB) + `Pillow` (10MB) |
| | • System dep: `tesseract-ocr` (15MB via apt-get) |
| | • **Total savings: ~2.5GB → ~25MB** |
| | • OCR quality for printed text remains equally good |
| **Files Changed** | `main.py`, `media_processor.py`, `requirements.txt`, `build.sh`, `Dockerfile` |
| **Lesson** | Always consider deployment constraints when choosing libraries. A 2GB dependency for OCR is overkill when Tesseract does the same job in 15MB. |

---

## Problem #9: Docker Build Failed — `libgl1-mesa-glx` Not Available

| | Details |
|---|---|
| **Problem** | Dockerfile had `apt-get install libgl1-mesa-glx` for OpenCV, but this package was **deprecated/removed** in Debian Trixie (the base image of `python:3.11-slim`). Build error: `E: Package 'libgl1-mesa-glx' has no installation candidate` |
| **Impact** | Docker build failed on Render even after fixing the PyTorch issue. |
| **Solution** | **Removed `libgl1-mesa-glx` entirely** — it was never needed because we use `opencv-python-headless` (not `opencv-python`). The headless version doesn't require any GUI/OpenGL system libraries. |
| **Files Changed** | `Dockerfile` |
| **Lesson** | Use `-headless` variants of packages for server deployment. Always test Docker builds with the exact base image the cloud platform uses. |

---

## Problem #10: System Off = Project Offline

| | Details |
|---|---|
| **Problem** | The project was only running locally via `python main.py`. When the user's laptop was off, the project was completely inaccessible. |
| **Impact** | No 24/7 availability — couldn't share the project URL with anyone for permanent access. |
| **Solution** | Deployed on **Render.com** (free tier): |
| | • Created `Dockerfile` with `python:3.11-slim` + Tesseract OCR |
| | • Created `render.yaml` deployment blueprint |
| | • Created `build.sh` for dependency installation |
| | • Created `.dockerignore` for faster builds |
| | • Updated `.gitignore` to exclude unnecessary files |
| | • Pushed to GitHub → Render auto-deploys from GitHub |
| | • App now live 24/7 with HTTPS URL |
| **Files Changed** | `Dockerfile` (NEW), `render.yaml` (NEW), `build.sh` (NEW), `.dockerignore` (NEW), `.gitignore`, `requirements.txt`, `config.yaml` |
| **Lesson** | Free cloud hosting exists — Render, Railway, PythonAnywhere. But heavy dependencies (like PyTorch) need to be optimized first. |

---

## 📊 Summary Table

| # | Problem | Category | Severity | Time to Fix |
|---|---------|----------|----------|-------------|
| 1 | Basic 2D UI | Frontend | Medium | ~30 min |
| 2 | No file validation | Backend | High | ~15 min |
| 3 | No body condition input | Full-stack | Critical | ~45 min |
| 4 | No cross-verification engine | Backend | Critical | ~60 min |
| 5 | No evidence media upload | Full-stack | High | ~45 min |
| 6 | Evidence gallery not in results | Frontend | Medium | ~20 min |
| 7 | ngrok command not working | DevOps | Low | ~10 min |
| 8 | EasyOCR too heavy for deploy | DevOps | Critical | ~15 min |
| 9 | Docker build failed (libgl1) | DevOps | Medium | ~5 min |
| 10 | System off = offline | DevOps | High | ~30 min |

---

## 🎯 Key Takeaways

1. **Input validation is non-negotiable** — garbage in = garbage out
2. **Cross-verification needs TWO data sources** — you can't detect tampering with only one side of the story
3. **Choose lightweight libraries for deployment** — PyTorch for OCR is overkill, Tesseract does the same job at 1% of the size
4. **Test Docker builds with exact production images** — packages get deprecated across OS versions
5. **`-headless` variants exist for a reason** — always use them on servers
6. **npm can shadow system binaries** — always verify `which` or `where` your command resolves to
7. **Premium UI builds trust** — users take your tool more seriously when it looks professional
8. **Plan for deployment from Day 1** — don't pick 2GB dependencies if you want free hosting

---

*Document created: May 2, 2026*  
*Project by: Raj Gautam (@RajGautam8113)*
