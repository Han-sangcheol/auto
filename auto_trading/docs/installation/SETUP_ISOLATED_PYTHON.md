# Isolated Python 32-bit Setup Guide

This guide explains how to install Python 32-bit for this project only, without affecting your existing Python 64-bit installation.

## Why This Approach?

- **Kiwoom Open API requires 32-bit Python** (COM object limitation)
- **Your system uses 64-bit Python** for other projects
- **Solution: Install 32-bit Python in a separate location** without adding to PATH
- **Result: Complete isolation** - no interference between projects

## Step-by-Step Installation

### Step 1: Download Python 32-bit

1. Visit: https://www.python.org/downloads/
2. Click on **Python 3.12.x** (recommended for stability)
3. Scroll down to "Files"
4. Download: **Windows installer (32-bit)**
   - Example: `python-3.12.x-amd64.exe` ❌ (this is 64-bit)
   - Example: `python-3.12.x.exe` ✅ (this is 32-bit)

### Step 2: Install Python 32-bit (Isolated)

**IMPORTANT: Custom installation to avoid PATH conflicts**

1. Run the installer
2. **UNCHECK** "Add Python to PATH" ❗ (Critical)
3. Click "Customize installation"
4. Next page - keep all features checked
5. **Advanced Options:**
   - Install for all users: ✅
   - **Custom install location:** `C:\Python32\`
   - Other options: default
6. Click "Install"

### Step 3: Verify Installation

Open PowerShell and run:

```powershell
C:\Python32\python.exe --version
```

Expected output:
```
Python 3.12.x (32-bit)
```

Verify it's 32-bit:
```powershell
C:\Python32\python.exe -c "import sys; print('64-bit' if sys.maxsize > 2**32 else '32-bit')"
```

Expected output:
```
32-bit
```

### Step 4: Clean Up Old Environment

Navigate to the project folder and remove the old 64-bit virtual environment:

```powershell
cd D:\cleonAI\auto_trading

# Remove old virtual environment
Remove-Item -Recurse -Force .venv
```

### Step 5: Create New 32-bit Virtual Environment

```powershell
# Create virtual environment with 32-bit Python
C:\Python32\python.exe -m venv .venv

# Verify
.\.venv\Scripts\python.exe -c "import sys; print('64-bit' if sys.maxsize > 2**32 else '32-bit')"
```

Expected output:
```
32-bit
```

### Step 6: Run Setup

```powershell
# Run setup with new 32-bit environment
.\setup.bat
```

or

```powershell
.\setup.ps1
```

### Step 7: Test Kiwoom API

```powershell
.\start.bat
```

or

```powershell
.\start.ps1
```

The Kiwoom API should now load successfully!

## Verification Checklist

- [ ] Python 32-bit installed in `C:\Python32\`
- [ ] NOT added to system PATH
- [ ] Old `.venv` folder removed
- [ ] New virtual environment created with 32-bit Python
- [ ] Packages installed successfully
- [ ] Program starts without COM errors

## Your System After Setup

```
System Python (64-bit): C:\Users\YourName\AppData\Local\Programs\Python\Python313\
  └─ Used by: Other projects (unchanged)

Isolated Python (32-bit): C:\Python32\
  └─ Used by: This project only (auto_trading)
      └─ Virtual Environment: D:\cleonAI\auto_trading\.venv\
```

## Troubleshooting

### Error: "python.exe not found"

Make sure you use the full path:
```powershell
C:\Python32\python.exe -m venv .venv
```

### Error: Still getting 64-bit

Delete `.venv` folder completely and recreate:
```powershell
Remove-Item -Recurse -Force .venv
C:\Python32\python.exe -m venv .venv
```

### Verify Current Python

Inside virtual environment:
```powershell
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
python -c "import sys; print('64-bit' if sys.maxsize > 2**32 else '32-bit')"
```

## Alternative: Portable Python

If you prefer, you can use **WinPython Portable 32-bit**:
- No installation required
- Completely portable
- Download from: https://winpython.github.io/

Extract to any folder and use the same approach.

## Next Steps

After successful setup:
1. Configure `.env` file
2. Install Kiwoom Open API+
3. Run the program
4. See `GETTING_STARTED.md` for complete guide

---

**Remember:** This setup ensures complete isolation. Your system Python 64-bit remains untouched!

