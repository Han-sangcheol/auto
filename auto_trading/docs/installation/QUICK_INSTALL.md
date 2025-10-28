# Quick Installation Guide - One Command Setup

The fastest way to set up CleonAI Auto-Trading system with Python 32-bit.

## 🚀 One-Command Installation (Recommended)

Open PowerShell as Administrator in the `auto_trading` folder and run:

```powershell
.\auto_setup_complete.ps1
```

**This single command will:**
- ✅ Download Python 3.12 32-bit automatically
- ✅ Install to C:\Python32\ (isolated, no system impact)
- ✅ Create virtual environment (32-bit)
- ✅ Install all packages
- ✅ Generate .env template
- ✅ **Fully automated - no user input required!**

**Time required:** 5-10 minutes

**Note:** If Python 32-bit is already installed at C:\Python32\, it will skip the download and use the existing installation.

---

## 📋 Step-by-Step Alternative

If you prefer manual control or the automatic script fails:

### Step 1: Install Python 32-bit

```powershell
.\install_python32.ps1
```

**What it does:**
- Downloads Python 3.12.8 32-bit
- Installs to C:\Python32\
- Does NOT modify system PATH
- Verifies installation

### Step 2: Setup Virtual Environment

```powershell
.\setup_python32.ps1
```

**What it does:**
- Creates 32-bit virtual environment
- Installs all packages
- Creates .env template

### Step 3: Configure Settings

Edit `.env` file:
```env
KIWOOM_ACCOUNT_NUMBER=your_account_number
KIWOOM_ACCOUNT_PASSWORD=your_4digit_password
WATCH_LIST=005930,000660,035720
USE_SIMULATION=True
```

### Step 4: Install Kiwoom API

See: [KIWOOM_API_SETUP.md](KIWOOM_API_SETUP.md)

### Step 5: Run

```powershell
.\start.ps1
```

---

## 🔧 Custom Installation Path

Want to install Python to a different location?

```powershell
.\install_python32.ps1 -InstallPath "D:\MyPython32" -PythonVersion "3.12.8"
```

Then update `setup_python32.ps1` to use your custom path.

---

## ✅ Verification

After installation, verify:

```powershell
# Check Python 32-bit
C:\Python32\python.exe --version
C:\Python32\python.exe -c "import sys; print('32-bit' if sys.maxsize <= 2**32 else '64-bit')"

# Check virtual environment
.\.venv\Scripts\python.exe -c "import sys; print('32-bit' if sys.maxsize <= 2**32 else '64-bit')"
```

Expected output:
```
Python 3.12.8
32-bit
32-bit
```

---

## 🆘 Troubleshooting

### "Execution policy" error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Not running as Administrator" warning

Right-click PowerShell → "Run as Administrator"

### Download fails

- Check internet connection
- Download manually from: https://www.python.org/downloads/
- Choose "Windows installer (32-bit)"
- Install to `C:\Python32\`
- UNCHECK "Add Python to PATH"

### Installation fails with error code

**1602**: Installation cancelled - Run script again
**1603**: Fatal error - Restart PC and retry
**1618**: Another installation running - Wait and retry

### Still getting 64-bit Python error

```powershell
# Remove old environment
Remove-Item -Recurse -Force .venv

# Recreate with 32-bit
C:\Python32\python.exe -m venv .venv

# Reinstall packages
.\setup.ps1
```

---

## 📚 More Help

- **Detailed Setup Guide**: [SETUP_ISOLATED_PYTHON.md](SETUP_ISOLATED_PYTHON.md)
- **Complete Tutorial**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **Problem Solving**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Kiwoom API**: [KIWOOM_API_SETUP.md](KIWOOM_API_SETUP.md)

---

## 🎯 Summary

**Simplest approach:**
```powershell
.\auto_setup_complete.ps1
```

**Done!** Your system Python 64-bit remains untouched.

The entire project uses isolated Python 32-bit at `C:\Python32\`.

