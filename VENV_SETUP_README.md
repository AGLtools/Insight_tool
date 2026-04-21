# AGL Analytics - Virtual Environment Setup

## 🎯 What Changed?

The application now uses an **isolated Python virtual environment** (`venv_agl/`) instead of installing packages directly into the system Python or the portable Python runtime. This ensures long-term safety and prevents dependency conflicts.

---

## 🚀 Getting Started

### First Time Setup

**Run this once:**
```bash
INSTALLATION.bat
```

This will:
1. Detect your Python installation (portable or system)
2. Create an isolated virtual environment (`venv_agl/`)
3. Install all required packages from `requirements.txt`
4. Verify everything is working

### Running the App

**Every time you want to use the app:**
```bash
Lancer_app.bat
```

This will:
1. Activate the isolated environment
2. Verify all dependencies are installed
3. Launch Streamlit on `http://localhost:8501`
4. Automatically open your browser

---

## 📦 What's in the Virtual Environment?

The `venv_agl/` folder contains a complete, isolated Python installation with only the packages your app needs:

- `streamlit` — Web dashboard framework
- `pandas` — Data manipulation
- `plotly` — Interactive charts
- `openpyxl` — Excel generation
- `python-pptx` — PowerPoint generation
- `kaleido` — Chart image export

### View Installed Packages

```bash
venv_agl\Scripts\pip.exe list
```

---

## 🛡️ Why This is Better

| Aspect | Before | Now |
|--------|--------|-----|
| **Isolation** | ❌ Shared with system | ✅ Isolated to app only |
| **Conflicts** | ❌ Other apps can break it | ✅ Completely independent |
| **Deprecation** | ❌ System updates affect app | ✅ App locked to specific versions |
| **Reproducibility** | ❌ Works on my machine | ✅ Works everywhere same way |
| **Cleanup** | ❌ Hard to uninstall | ✅ Delete `venv_agl/` folder |

---

## 🔄 Adding New Packages

If you need to add a new Python package:

1. **Add to `requirements.txt`:**
   ```
   streamlit
   pandas
   plotly
   openpyxl
   python-pptx
   kaleido
   my-new-package  ← Add here
   ```

2. **Update your environment:**
   ```bash
   venv_agl\Scripts\pip.exe install -r requirements.txt
   ```

   Or just run `INSTALLATION.bat` again.

---

## 🗑️ Removing/Updating

### Completely reset the environment:
```bash
rmdir /s /q venv_agl
INSTALLATION.bat
```

### Update packages without resetting:
```bash
venv_agl\Scripts\pip.exe install --upgrade -r requirements.txt
```

---

## 📋 File Structure

```
c:\AGL Analytics\
├── app.py                        ← Main application
├── requirements.txt              ← Package list
├── INSTALLATION.bat              ← Initial setup (run once)
├── Lancer_app.bat               ← Launch app (run each time)
├── setup_venv.bat               ← Manual venv setup (optional)
├── venv_agl\                    ← Virtual environment (auto-created)
│   ├── Scripts\
│   │   ├── python.exe           ← Isolated Python
│   │   └── pip.exe              ← Package manager
│   └── Lib\                     ← Installed packages
└── ... (other files)
```

---

## ✅ Verification

### Check if venv is working:

```bash
venv_agl\Scripts\python.exe --version
venv_agl\Scripts\pip.exe list
```

### Check app runs:

```bash
Lancer_app.bat
```

Should open Streamlit at `http://localhost:8501`

---

## 🔧 Troubleshooting

### "Environnement virtuel non trouve"
→ Run `INSTALLATION.bat` first

### Packages missing after update
→ Run `INSTALLATION.bat` again

### Streamlit port in use (8501)
→ Kill other Streamlit instances or use custom port:
```bash
venv_agl\Scripts\python.exe -m streamlit run app.py --server.port 8502
```

---

## 📚 Resources

- **Python venv docs**: https://docs.python.org/3/library/venv.html
- **Streamlit docs**: https://docs.streamlit.io
- **requirements.txt format**: https://pip.pypa.io/en/latest/reference/requirements-file-format/

---

**Created**: April 2026  
**Purpose**: Long-term dependency safety and application isolation
