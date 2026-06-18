# Flux - Professional Maya ↔ Blender Asset Pipeline (FBX)

<img width="800" height="450" alt="flux" src="https://github.com/user-attachments/assets/ae64dbee-fcdb-4edf-92ac-bd8be7d09889" />


Flux is a high-performance standalone desktop utility and launchpad designed for professional 3D artists, game developers, and technical directors. It facilitates seamless, loss-free, single-click asset transfers between Autodesk Maya and Blender.

By utilizing a sidecar metadata manifest workflow, Flux bypasses traditional FBX format limitations, preserving and mapping critical DCC parameters perfectly across both hosts.

---

## 💎 Product Features & Design
- **Single-Click Synchronizations**: Perform bi-directional roundtrips (`Maya ➔ Blender` or `Blender ➔ Maya`) automatically.
- **Data Preservation Engine**:
  - **UV Layouts & Custom Shaders**: Retain UV coordinate systems and mapping data. Original shader inputs and material slots are automatically remapped to prevent duplicate materials (e.g. `.001` duplicates).
  - **Pivots & Local Transforms**: Tracks scale/rotate pivots in Maya and object origins in Blender using dynamic coordinates.
  - **Vertex Groups & Weights**: Retains and restores custom vertex weights/groups on import.
  - **Viewport Edge Hardness**: Edge crease weightings and hard/soft viewport shading boundaries are translated perfectly.
  - **Activity Console**: Real-time validation logs and subprocess trackers directly inside the launcher.

---

## 🚀 Quick Start

1. **Initialize Flux**:
   - Double-click `Launch Flux.bat`
   - Or run in terminal:
     ```powershell
     python run_flux.py
     ```

2. **Configure DCC Locations**:
   - Go to the **Settings** tab.
   - Specify your `maya.exe` and `blender.exe` executable locations.
   - Choose your preferred **Exchange Directory** (recommends local SSD storage for fast FBX caching).
   - Click **Save Settings**.

3. **Bootstrap Your Creative Environment**:
   - From the launcher terminal tab, click **Launch Maya** and/or **Launch Blender**.
   - Flux opens your target DCCs and automatically registers background command servers.
   - *Alternative (Manual connection)*: Click **Copy For Maya** or **Copy For Blender** from Settings and execute the script in your DCC script editor.

4. **Synchronize mesh assets**:
   - Make your mesh selections in the source DCC.
   - Select the target direction switcher in Flux (`Maya ➔ Blender` or `Blender ➔ Maya`).
   - Click **ROUNDTRIP SYNC** to instantly export and import.

---

## ⚙ Pipeline Configuration Options

Configure policies and overrides in the **Advanced Options** drawer:
- **Update Existing Mesh by Name**: Replaces geometry data in place on duplicate naming hits, leaving existing material network assignments stable.
- **Sync Destination Transforms and Pivots**: Align target coordinates to stamp positioning and pivot points with the source geometry.
- **Manual Actions**: Perform independent manual exports/imports without triggers.

---

## 🛠 Developer Testing & Staging

Staging the PyQt6 runtimes and running tests can be done directly from the root workspace:

- **Run Staging Script**:
  ```powershell
  python scripts/stage_pyqt6_runtime.py
  ```
- **Execute Core Smoke Tests**:
  ```powershell
  python scripts/smoke_test.py
  ```
