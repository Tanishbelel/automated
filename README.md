# Project Setup Guide (Readme2)

This guide provides step-by-step instructions to set up and run the automated metadata extraction and cleaning project.

## 📋 Prerequisites

Before starting, ensure you have the following installed:
- **Python 3.13+**
- **Redis Server** (Required for background tasks, caching, and Celery broker)
- **Tesseract OCR Engine** (Required for metadata extraction and redaction)
  - **Mac:** `brew install tesseract`
  - **Linux:** `sudo apt install tesseract-ocr`
  - **Windows:** Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.
- **Google Chrome** (For the extension)

---

## 🚀 Backend Setup (Django & Celery)

1. **Navigate to the Project Root:**
   ```bash
   cd "mini proj/automated"
   ```

2. **Create and Activate Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables (CRITICAL for Mac):**
   Set the following variables in your terminal session or `.env` file:
   ```bash
   export PYTHONPATH=$PYTHONPATH:.
   export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
   ```

5. **Run Migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start Redis Server:**
   Ensure Redis is running in a separate terminal:
   ```bash
   redis-server
   ```

7. **Start Celery Worker:**
   Open a NEW terminal, activate `venv`, set environment variables, and run:
   ```bash
   celery -A pipeline.bulk_queue worker --loglevel=info
   ```

8. **Start Django Development Server:**
   ```bash
   python manage.py runserver
   ```
   The API will be available at `http://127.0.0.1:8000/api/`.

---

## 🌐 Frontend Setup (Chrome Extension)

1. Open **Google Chrome**.
2. Navigate to `chrome://extensions/`.
3. Enable **"Developer mode"** (toggle in the top right corner).
4. Click **"Load unpacked"**.
5. Select the `extension` folder inside the project directory (`mini proj/automated/extension`).
6. The extension icon should now appear in your browser toolbar.

---

## 🛠️ Key Features & Usage

### 🔍 Single File Analysis
- Open the extension popup.
- Select a file (Images, PDFs, etc.).
- Click **"Analyze"** to see extracted metadata and risk scores.
- Click **"Clean Metadata"** to generate a sanitized version.
- Use **"Secure Share"** to generate a password-protected link.

### 📦 Bulk Pipeline
- Select multiple files in the extension.
- Click **"Start Pipeline"**.
- The system will process files in batches using Celery.
- Download the final results as a single **ZIP archive**.

---

## ⚠️ Troubleshooting

- **Celery Tasks Not Running:** Ensure `redis-server` is active and the Celery worker is running in a separate terminal.
- **Tesseract Not Found:** Verify `tesseract --version` in your terminal. If installed in a non-standard path, update `detector.py`.
- **CORS Issues:** The backend is configured to allow `chrome-extension://` origins. 
- **Import Errors:** Always ensure `PYTHONPATH` includes the current directory.
- **Mac Fork Error:** If you see a crash related to `fork()`, ensure `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` is set.

---

## 📂 Project Structure
- `main/`: Core Django app logic, models, and views.
- `extension/`: Chrome extension source code (HTML/JS/CSS).
- `pipeline/`: Bulk processing logic and Celery tasks (`bulk_queue.py`).
- `redaction/`: AI-powered metadata detection and removal using OpenCV and Tesseract.
- `automated/`: Project settings and URL configurations.
