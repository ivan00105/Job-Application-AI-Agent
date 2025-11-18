# Setup Guide

## 1. Backend

```bash
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

Backend runs on `http://localhost:8000`

## 2. Frontend

```bash
npm run dev
```

Frontend runs on `http://localhost:5173`

## 3. Chrome Extension

```bash
cd extension
pip install Pillow
python create-icons.py
```

Then:
1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Select the `extension/` folder

Done!

## Usage

1. Log into web app (`http://localhost:5173`)
2. Navigate to any job application page
3. Look for purple "AI Auto-Fill" button (bottom-right)
4. Click it to auto-fill the form
5. Review and submit

## Troubleshooting

### Button not appearing
- Reload page (Ctrl+R)
- Check extension enabled at `chrome://extensions/`

### ERR_BLOCKED_BY_CLIENT
- Disable ad blocker for `localhost:5173`

### Not logged in error
- Go to `localhost:5173` and log in
- Token syncs automatically

That's it!


