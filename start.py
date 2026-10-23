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
import argparse
import http.server
import socketserver
import functools
import json

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
    """Custom handler that serves from the frontend directory with runtime env injection"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        req_path = self.path.split("?")[0]
        if req_path.endswith(".html") or req_path in ("/", ""):
            filename = req_path.lstrip("/") or "index.html"
            filepath = os.path.join(FRONTEND_DIR, filename)
            if os.path.exists(filepath) and os.path.isfile(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                cesium_token = os.getenv("CESIUM_ION_TOKEN", "")
                config_script = f'<script>window.SDARS_CONFIG = window.SDARS_CONFIG || {{}}; window.SDARS_CONFIG.CESIUM_ION_TOKEN = {json.dumps(cesium_token)};</script>'
                if "<head>" in content:
                    content = content.replace("<head>", f"<head>\n    {config_script}", 1)
                else:
                    content = f"{config_script}\n{content}"
                data = content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        super().do_GET()

def start_backend(is_dev: bool = False):
    """Start the FastAPI backend server"""
    host = "0.0.0.0" if is_dev else "127.0.0.1"
    mode_str = "DEV MODE (0.0.0.0 with --reload)" if is_dev else "PROD MODE (127.0.0.1)"
    print(f"🚀 Starting Backend API [{mode_str}] on http://{host}:{BACKEND_PORT}...")
    
    backend_env = os.environ.copy()
    backend_env["PYTHONUTF8"] = "1"
    backend_env["PYTHONIOENCODING"] = "utf-8"

    cmd = [
        sys.executable, "-m", "uvicorn", 
        "api.server:app", 
        "--host", host, 
        "--port", str(BACKEND_PORT),
    ]
    if is_dev:
        cmd.append("--reload")

    # Run uvicorn as a subprocess with the correct working directory
    subprocess.run(
        cmd,
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
    parser = argparse.ArgumentParser(description="SDARS - Complete System Launcher")
    parser.add_argument(
        "--dev", 
        action="store_true", 
        help="Run in development mode: bind to 0.0.0.0 and enable uvicorn --reload"
    )
    args = parser.parse_args()

    backend_host = "0.0.0.0" if args.dev else "127.0.0.1"

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🛰️  SDARS - Complete System Launcher                       ║
    ║   AI-Based Satellite-Driven Smart Disaster Alert System     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"📍 Backend API:  http://{backend_host}:{BACKEND_PORT}")
    print(f"📍 Frontend:     http://127.0.0.1:{FRONTEND_PORT}")
    print(f"📍 API Docs:     http://{backend_host}:{BACKEND_PORT}/docs")
    print(f"📍 Mode:         {'DEVELOPMENT (--dev)' if args.dev else 'DEFAULT (127.0.0.1)'}")
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
        start_backend(is_dev=args.dev)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down SDARS...")
        print("Goodbye! 👋")
