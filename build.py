import os
import sys
import subprocess

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtCore import QByteArray
    from icons import _ICONS
except ImportError:
    print("Missing PyQt6. Please run 'pip install PyQt6' to build the icon.")
    sys.exit(1)

def generate_icon():
    # We need a headless QApplication to use QPixmap
    app = QApplication(sys.argv)
    
    # We grab the 'music' icon SVG map and color it purple just like the app UI
    svg_str = _ICONS["music"].format(color="#8B5CF6")
    # Scale it up to 256x256 for high quality Windows desktop icons
    svg_str = svg_str.replace("viewBox", 'width="256" height="256" viewBox')
    
    arr = QByteArray(svg_str.encode('utf-8'))
    pm = QPixmap()
    pm.loadFromData(arr, "SVG")
    
    icon_path = "app_icon.ico"
    # PyQt6 officially supports writing out native .ico format directly!
    success = pm.save(icon_path, "ICO")
    if not success:
        print("Fallback to PNG icon rendering...")
        icon_path = "app_icon.png"
        pm.save(icon_path, "PNG")
        
    return icon_path

def main():
    print("🎵 Building Soundpad.exe...")
    print("Generating official application icon from SVG format...")
    icon_path = generate_icon()
    print(f"✔ Icon created at {icon_path}")

    print("✔ Initiating PyInstaller build...")
    
    # PyInstaller command list
    cmd = [
        "pyinstaller",
        "--noconsole",          # Hide terminal window background
        "--onefile",            # Bundle into a single standalone .exe
        "--name", "Soundpad",   # Name of the executable output
        f"--icon={icon_path}",  # Apply our freshly generated icon!
        "--clean",              # Discard old build caches
        "--noconfirm",          # Replace existing output files automatically
        "app.py"
    ]
    
    subprocess.run(cmd)
    
    print("\n✅ Build absolutely complete!")
    print("Check the 'dist' folder for your final 'Soundpad.exe' program.")

if __name__ == "__main__":
    main()
