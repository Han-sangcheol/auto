# Installation Scripts Reference

Complete guide to all installation and setup scripts.

## 📦 Available Scripts

### 1. 🚀 `auto_setup_complete.ps1` - ONE-CLICK SETUP (RECOMMENDED)

**Purpose:** Complete automated installation from scratch.

**What it does:**
- Downloads Python 3.12 32-bit automatically
- Installs to C:\Python32\
- Creates virtual environment (32-bit)
- Installs all packages
- Sets up .env template
- **Fully automated - no user input required!**

**Usage:**
```powershell
# Run as Administrator
.\auto_setup_complete.ps1
```

**How it works:**
1. Calls `install_python32.ps1 -Automated`
2. Calls `setup_python32.ps1 -Automated`
3. Reports final status

**Time:** 5-10 minutes  
**Prerequisites:** Internet connection, Administrator rights  
**System Impact:** None (isolated installation)

**Note:** If Python 32-bit already exists at C:\Python32\, it automatically uses it without prompting.

---

### 2. 🔽 `install_python32.ps1` - PYTHON INSTALLER

**Purpose:** Downloads and installs Python 32-bit only.

**What it does:**
- Downloads Python 3.12.8 32-bit from python.org
- Installs to C:\Python32\ (customizable)
- Does NOT modify system PATH
- Verifies installation

**Usage:**
```powershell
# Interactive mode (default)
.\install_python32.ps1

# Automated mode (no prompts)
.\install_python32.ps1 -Automated

# Custom installation path
.\install_python32.ps1 -InstallPath "D:\MyPython" -PythonVersion "3.12.8"

# Automated with custom path
.\install_python32.ps1 -InstallPath "D:\MyPython" -Automated
```

**Parameters:**
- `InstallPath`: Installation directory (default: C:\Python32)
- `PythonVersion`: Python version (default: 3.12.8)
- `Automated`: Skip all user prompts (for automated scripts)

**Time:** 3-5 minutes  
**Size:** ~25 MB download

---

### 3. ⚙️ `setup_python32.ps1` - ENVIRONMENT SETUP

**Purpose:** Creates virtual environment with existing Python 32-bit.

**Prerequisites:** Python 32-bit already installed at C:\Python32\

**What it does:**
- Verifies Python 32-bit installation
- Removes old 64-bit virtual environment (if exists)
- Creates new 32-bit virtual environment
- Installs all packages from requirements.txt
- Creates .env template

**Usage:**
```powershell
# Interactive mode (default)
.\setup_python32.ps1

# Automated mode (no prompts)
.\setup_python32.ps1 -Automated
```

**Parameters:**
- `Automated`: Skip all user prompts, auto-remove old environment

**Time:** 5-10 minutes (package installation)

---

### 4. 📝 `setup.ps1` / `setup.bat` - STANDARD SETUP

**Purpose:** Setup with your current Python (use after Python 32-bit is active).

**What it does:**
- Creates virtual environment
- Installs packages
- Creates logs directory
- Creates .env template

**Usage:**
```powershell
# PowerShell
.\setup.ps1

# CMD
setup.bat
```

**Note:** Use ONLY if .venv is already 32-bit!

---

### 5. ▶️ `start.ps1` / `start.bat` - RUN PROGRAM

**Purpose:** Starts the auto-trading program.

**Prerequisites:**
- Python 32-bit environment set up
- .env file configured
- Kiwoom API installed

**What it does:**
- Pre-flight checklist
- Activates virtual environment
- Runs main.py

**Usage:**
```powershell
# PowerShell
.\start.ps1

# CMD
start.bat
```

---

## 🎯 Which Script to Use?

### First-Time Setup (Never installed Python 32-bit)

```
✨ ONE COMMAND:
   .\auto_setup_complete.ps1
```

**OR step by step:**

```
1️⃣ .\install_python32.ps1      (Install Python 32-bit)
2️⃣ .\setup_python32.ps1         (Create environment)
3️⃣ Edit .env file               (Configure)
4️⃣ Install Kiwoom API           (Download + Install)
5️⃣ .\start.ps1                  (Run)
```

### Python 32-bit Already Installed

```
1️⃣ .\setup_python32.ps1         (Create environment)
2️⃣ Edit .env file               (Configure)
3️⃣ .\start.ps1                  (Run)
```

### Environment Already Set Up

```
1️⃣ .\start.ps1                  (Run)
```

### Reinstall Environment (Keep Python)

```
1️⃣ Remove-Item -Recurse .venv  (Delete old)
2️⃣ .\setup_python32.ps1         (Recreate)
3️⃣ .\start.ps1                  (Run)
```

---

## 🔧 Script Parameters

### install_python32.ps1

```powershell
# Install to custom path
.\install_python32.ps1 -InstallPath "D:\Python32"

# Install specific version
.\install_python32.ps1 -PythonVersion "3.12.7"

# Both
.\install_python32.ps1 -InstallPath "D:\Python32" -PythonVersion "3.12.7"
```

---

## ✅ Verification Commands

### Check Python Installation

```powershell
# Check if Python 32-bit is installed
C:\Python32\python.exe --version
C:\Python32\python.exe -c "import sys; print('32-bit' if sys.maxsize <= 2**32 else '64-bit')"
```

### Check Virtual Environment

```powershell
# Check if venv is 32-bit
.\.venv\Scripts\python.exe -c "import sys; print('32-bit' if sys.maxsize <= 2**32 else '64-bit')"
```

### Check Packages

```powershell
# Activate and check
.\.venv\Scripts\Activate.ps1
pip list
```

---

## 🆘 Troubleshooting

### "Execution policy" error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "Not Administrator" warning

Right-click PowerShell → "Run as Administrator"

### Download fails

- Check internet connection
- Firewall may be blocking
- Try manual download from python.org

### Still 64-bit after setup

```powershell
# Complete cleanup and restart
Remove-Item -Recurse -Force .venv
C:\Python32\python.exe -m venv .venv
.\setup.ps1
```

### Python 32-bit not found

Check installation:
```powershell
Test-Path C:\Python32\python.exe
```

If false, run:
```powershell
.\install_python32.ps1
```

---

## 📚 Related Documentation

- **Quick Install**: [QUICK_INSTALL.md](QUICK_INSTALL.md)
- **Detailed Setup**: [SETUP_ISOLATED_PYTHON.md](SETUP_ISOLATED_PYTHON.md)
- **Complete Guide**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 💡 Pro Tips

1. **Always use PowerShell (not CMD)** for better error messages
2. **Run as Administrator** for installation scripts
3. **Check 32-bit** before running program: `.venv\Scripts\python.exe -c "import sys; print(sys.maxsize)"`
4. **Keep C:\Python32\** - other projects can use it too (isolated)
5. **Backup .env** - contains your account information

---

## 🎯 Quick Reference

| Goal | Command |
|------|---------|
| Complete setup (first time) | `.\auto_setup_complete.ps1` |
| Install Python only | `.\install_python32.ps1` |
| Setup environment | `.\setup_python32.ps1` |
| Run program | `.\start.ps1` |
| Verify 32-bit | `.venv\Scripts\python.exe -c "import sys; print('32-bit' if sys.maxsize <= 2**32 else '64-bit')"` |

---

**Remember:** These scripts are designed to be **completely isolated** from your system Python. Your other Python projects will not be affected!

