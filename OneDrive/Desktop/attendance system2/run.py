"""
========================================================
 Smart AI Attendance System - Launcher
 Developed for minor project
========================================================
"""

import os
import sys
import time

# Optional: Display loading message
print("🚀 Launching Smart AI Attendance System...")
time.sleep(0.8)

# Ensure required files exist
required_files = ["ui.py", "backend.py"]
missing = [f for f in required_files if not os.path.exists(f)]
if missing:
    print(f"❌ Missing required files: {', '.join(missing)}")
    sys.exit(1)

try:
    import ui
except ImportError as e:
    print(f"⚠️ Failed to start UI module: {e}")
    sys.exit(1)

if __name__ == "__main__":
    print("✅ Smart AI Attendance System started successfully.")
    # The UI auto-runs when imported
    pass
