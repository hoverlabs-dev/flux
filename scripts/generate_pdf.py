import sys
from pathlib import Path

# Insert vendored PyQt6 runtime path matching the current Python version
py_tag = f"py{sys.version_info.major}{sys.version_info.minor}"
vendored_path = Path(__file__).resolve().parents[1] / "vendor" / "python" / py_tag
if str(vendored_path) not in sys.path:
    sys.path.insert(0, str(vendored_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPdfWriter, QTextDocument, QPageLayout, QPageSize
from PyQt6.QtCore import QMarginsF

def main():
    app = QApplication([])
    
    doc = QTextDocument()
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            color: #1e293b;
            margin: 30px;
            line-height: 1.5;
        }
        h1 {
            color: #1e3a8a;
            font-size: 20pt;
            border-bottom: 2px solid #3b82f6;
            padding-bottom: 6px;
            margin-top: 0;
            margin-bottom: 4px;
        }
        .subtitle {
            font-size: 10.5pt;
            color: #475569;
            margin-bottom: 20px;
        }
        h2 {
            color: #2563eb;
            font-size: 13pt;
            margin-top: 20px;
            margin-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 3px;
        }
        .accent {
            color: #2563eb;
            font-weight: bold;
        }
        .card {
            background-color: #f8fafc;
            border-left: 4px solid #3b82f6;
            padding: 12px;
            margin: 14px 0;
            border-radius: 4px;
        }
        .step-num {
            background-color: #3b82f6;
            color: white;
            display: inline-block;
            width: 20px;
            height: 20px;
            line-height: 20px;
            text-align: center;
            border-radius: 10px;
            font-weight: bold;
            margin-right: 6px;
            font-size: 9pt;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
        }
        th {
            background-color: #f1f5f9;
            text-align: left;
            padding: 8px;
            border-bottom: 2px solid #e2e8f0;
            font-weight: 600;
        }
        td {
            padding: 8px;
            border-bottom: 1px solid #e2e8f0;
        }
        code {
            font-family: 'Consolas', monospace;
            background-color: #f1f5f9;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 9pt;
        }
        .footer {
            margin-top: 40px;
            font-size: 8.5pt;
            color: #64748b;
            text-align: center;
            border-top: 1px solid #e2e8f0;
            padding-top: 12px;
        }
        ul, ol {
            margin-top: 4px;
            margin-bottom: 4px;
            padding-left: 20px;
        }
        li {
            margin-bottom: 4px;
        }
    </style>
    </head>
    <body>

    <h1>Portal: Maya &harr; Blender Asset Bridge</h1>
    <div class="subtitle">Developed by Jaisurya C &bull; Quick Artist Reference Guide &bull; Bi-directional Mesh Transfer Tool</div>

    <div class="card">
        <span class="accent">⚡ Quick Start Connection:</span>
        <ol>
            <li>Copy this folder into your local</li>
            <li>Launch the Portal application using <code>portal.exe</code>.</li>
            <li>Click <b>Launch Maya</b> and <b>Launch Blender</b> from the main page to open your editors.</li>
            <li>The connection starts automatically in the background—no manual script setup is required!</li>
        </ol>
    </div>

    <h2>🚀 Transferring Assets Step-by-Step</h2>

    <div style="margin-bottom: 12px;">
        <p><span class="step-num">1</span> <b>Choose Flow Direction:</b> Inside the Portal's main page, select either:</p>
        <ul>
            <li><span style="color:#2563eb; font-weight:700;">Maya ➔ Blender</span> (transfers selection from Maya into Blender)</li>
            <li><span style="color:#d97706; font-weight:700;">Blender ➔ Maya</span> (transfers selection from Blender into Maya)</li>
        </ul>
    </div>

    <div style="margin-bottom: 12px;">
        <p><span class="step-num">2</span> <b>Select Viewport Objects:</b> Select the polygon meshes inside your source application's viewport.</p>
    </div>

    <div style="margin-bottom: 12px;">
        <p><span class="step-num">3</span> <b>Roundtrip Sync:</b> Press the large blue <b>ROUNDTRIP SYNC</b> button in the Portal dashboard. The meshes will export and instantly load into the target application.</p>
    </div>

    <div class="footer">
        Tech Art 2026
    </div>

    </body>
    </html>
    """
    
    doc.setHtml(html_content)
    
    output_path = Path(__file__).resolve().parents[1] / "dist" / "Portal_Artist_Guide.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    writer = QPdfWriter(str(output_path))
    
    doc.print(writer)
    if output_path.exists():
        print(f"PDF successfully generated at: {output_path}")
    else:
        print("Failed to generate PDF.")

if __name__ == "__main__":
    main()
