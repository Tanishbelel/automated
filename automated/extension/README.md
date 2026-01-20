# 🛡️ Metadata Removal Tool - Chrome Extension

A browser extension that helps you analyze and remove hidden metadata from your files to protect your privacy.

## Features

### 📊 Metadata Removal
- **📁 File Upload**: Drag & drop or click to upload images and PDFs
- **🔍 Metadata Analysis**: Detect hidden metadata like GPS location, device info, author details
- **⚠️ Privacy Risk Score**: Get a risk assessment score (0-100)
- **🧹 Automatic Cleaning**: Download files with metadata stripped
- **🔗 Share Clean Files**: Generate shareable links for cleaned files
- **🎯 Platform Optimization**: Optimize for Instagram, Facebook, Twitter, LinkedIn

### 🔐 File Encryption (NEW!)
- **🔒 Local Encryption**: Encrypt any file with AES-256-GCM (military-grade)
- **🔓 Local Decryption**: Decrypt files with the correct password
- **⚡ 100% Offline**: Files never leave your device - true privacy
- **📤 Share Securely**: Share encrypted files via any medium (email, WhatsApp, USB, etc.)

## Supported File Types

- JPEG / JPG images
- PNG images
- GIF images
- WebP images
- TIFF images
- PDF documents

## Prerequisites

Before using this extension, you need to have the Django backend server running:

1. **Install Python dependencies**:
   ```bash
   cd automated
   pip install -r requirements.txt
   ```

2. **Run the Django server**:
   ```bash
   python manage.py runserver
   ```
   
   The server should be running at `http://127.0.0.1:8000`

## Installation

### Load as Unpacked Extension (Developer Mode)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `extension` folder from this project
5. The extension icon will appear in your browser toolbar

### Verify Installation

1. Click the extension icon in the toolbar
2. You should see "Server connected" status if the Django server is running
3. If it shows "Server offline", make sure to start the Django server first

## Usage

1. **Start the Server**: Make sure Django backend is running
2. **Click the Extension Icon**: Opens the popup interface
3. **Upload a File**: Click or drag a file into the upload area
4. **Select Platform** (optional): Choose optimization for specific social media
5. **Click Analyze**: The extension will analyze the file for metadata
6. **Review Results**: See the risk score and detected metadata
7. **Download Clean**: Click to download the file with metadata removed
8. **Share** (optional): Generate a shareable link for the clean file

## Project Structure

```
extension/
├── manifest.json      # Extension configuration (Manifest V3)
├── popup.html         # Main popup interface
├── popup.css          # Styling (dark theme with gradients)
├── popup.js           # JavaScript logic & API integration
├── icons/             # Extension icons
│   ├── icon16.png
│   ├── icon32.png
│   ├── icon48.png
│   └── icon128.png
└── README.md          # This file
```

## API Endpoints Used

The extension communicates with the Django REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health/` | GET | Check server connection |
| `/api/analyze/` | POST | Upload and analyze file |
| `/api/clean/` | POST | Download cleaned file |
| `/api/make-public/{id}/` | POST | Generate share link |

## Troubleshooting

### Extension shows "Server offline"
- Make sure Django server is running on `http://127.0.0.1:8000`
- Check if the server has any errors in the terminal

### File upload fails
- Ensure file is under 50MB
- Check if file type is supported (images or PDF)
- Verify server is running and connected

### Download doesn't work
- Check browser popup blocker settings
- Ensure the analysis completed successfully

## Security Note

This extension only communicates with your local Django server (`127.0.0.1:8000`). Your files are processed locally and are not sent to any external servers.

## License

MIT License - Feel free to use and modify!

---

Made with ❤️ for your privacy
