"""
SDARS One-Command Starter Script
Starts both the FastAPI backend and serves the frontend
"""
import subprocess
import threading
import webbrowser
import time
import os
import sys
import http.server
import socketserver
import functools

# Configure UTF-8 encoding for standard output on Windows
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 5500
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that serves from the frontend directory"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

def start_backend():
    """Start the FastAPI backend server"""
    print(f"🚀 Starting Backend API on http://localhost:{BACKEND_PORT}...")
    
    backend_env = os.environ.copy()
    backend_env["PYTHONUTF8"] = "1"
    backend_env["PYTHONIOENCODING"] = "utf-8"

    # Run uvicorn as a subprocess with the correct working directory
    subprocess.run(
        [
            sys.executable, "-m", "uvicorn", 
            "api.server:app", 
            "--host", "0.0.0.0", 
            "--port", str(BACKEND_PORT),
            "--reload"
        ],
        cwd=BACKEND_DIR,  # Set working directory without os.chdir
        env=backend_env
    )

def start_frontend():
    """Start a simple HTTP server for the frontend"""
    print(f"🌐 Starting Frontend on http://127.0.0.1:{FRONTEND_PORT}...")
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", FRONTEND_PORT), FrontendHandler) as httpd:
        httpd.serve_forever()

def open_browser():
    """Open the frontend in the default browser after a short delay"""
    time.sleep(2)  # Wait for servers to start
    print(f"\n✨ Opening browser at http://127.0.0.1:{FRONTEND_PORT}")
    webbrowser.open(f"http://127.0.0.1:{FRONTEND_PORT}")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🛰️  SDARS - Complete System Launcher                       ║
    ║   AI-Based Satellite-Driven Smart Disaster Alert System     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"📍 Backend API:  http://127.0.0.1:{BACKEND_PORT}")
    print(f"📍 Frontend:     http://127.0.0.1:{FRONTEND_PORT}")
    print(f"📍 API Docs:     http://127.0.0.1:{BACKEND_PORT}/docs")
    print("\n⏳ Starting servers...\n")
    print("-" * 60)
    
    # Start frontend in a separate thread (uses explicit directory, no os.chdir)
    frontend_thread = threading.Thread(target=start_frontend, daemon=True)
    frontend_thread.start()
    
    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start backend in the main thread (blocking, uses cwd parameter)
    try:
        start_backend()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down SDARS...")
        print("Goodbye! 👋")
