# Contributing to Flux

Thank you for your interest in contributing to Flux! This project is open source and we welcome contributions from technical artists, developers, and users.

Here is a guide on how to set up your environment, test your changes, and submit code.

---

## 🛠️ Development Setup

Flux is written in **Python 3.10+** using **PyQt6** for the user interface.

### 1. Prerequisites
- Python 3.10 or 3.11 installed on your system.
- Git.
- (Optional) Autodesk Maya and Blender to test integration features.

### 2. Clone the Repository
```powershell
git clone https://github.com/hoverlabs-dev/flux.git
cd flux
```

### 3. Stage the Vendored Runtimes
To prevent dependency issues across different DCC (Digital Content Creation) environments, Flux vendors its PyQt6 runtime binaries. Run the staging script to download and structure the PyQt6 runtime for your Python version:
```powershell
python scripts/stage_pyqt6_runtime.py
```

### 4. Running Flux Locally
You can run the application directly from the source code without compilation:
```powershell
python run_flux.py
```

---

## 📐 Coding Standards

- **Code Style**: We use `ruff` to lint and format our codebase.
- **Line Length**: Set to a maximum of `120` characters.
- **Typing**: Use standard Python type hints where possible (e.g. `from __future__ import annotations`).
- **Clean Code**: Avoid hardcoding configurations. Save preferences inside the dataclass settings system in `flux/config.py`.

---

## 🧪 Testing Your Changes

Before submitting a pull request, ensure that your changes pass the core logic tests:

```powershell
python scripts/smoke_test.py
```

This validates manifest reading/writing, matrix transformations, custom properties tracking, and path overrides.

---

## 📦 Building Executables & Installer

If you make changes to the app wrapper or the startup configurations, compile a local release to test:

### 1. PyInstaller Build
Compile the application bundle into `dist/Flux.dist`:
```powershell
python -m PyInstaller flux.spec --noconfirm
```

### 2. Compile Windows Installer
Compile the installer setup using the Inno Setup Compiler (`ISCC.exe`):
```powershell
& "C:\Users\<username>\AppData\Local\Programs\Inno Setup 6\ISCC.exe" flux_installer.iss
```
This produces `dist/Flux_Installer.exe`.

---

## 🤝 How to Submit a Pull Request

1. Fork the repository on GitHub.
2. Create a new feature branch (`git checkout -b feature/amazing-feature`).
3. Make your changes and commit them with descriptive commit messages.
4. Run the smoke tests to ensure everything is stable.
5. Push to your branch (`git push origin feature/amazing-feature`).
6. Open a Pull Request on the main repository.
