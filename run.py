"""
DocuForge AI — Single command project launcher.

Starts FastAPI backend, Celery worker, and React frontend in the correct
order with appropriate delays. Automatically opens the browser when ready.
Run with: python run.py
"""

import subprocess
import sys
import os
import time
import signal
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"
ENV_FILE = ROOT / ".env"
NODE_MODULES = FRONTEND / "node_modules"

processes: list[subprocess.Popen] = []


def kill_all(sig=None, frame=None) -> None:
    """
    Terminate all child processes cleanly on shutdown signal.
    
    Args:
        sig: Signal number (unused)
        frame: Stack frame (unused)
    """
    print("\n\nShutting down DocuForge AI...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    print("All services stopped. Goodbye!")
    sys.exit(0)


def check_prerequisites() -> None:
    """
    Verify required files and directories exist before attempting startup.
    Exits with a helpful message if any prerequisite is missing.
    """
    if not ENV_FILE.exists():
        print("ERROR: .env file not found.")
        print("\nRun these commands:")
        print("  copy .env.example .env")
        print("  # Then edit .env and add:")
        print("  # GEMINI_API_KEY=your_api_key")
        print("  # UPSTASH_REDIS_URL=rediss://your_upstash_url")
        sys.exit(1)

    if not NODE_MODULES.exists():
        print("ERROR: frontend/node_modules not found.")
        print("\nRun: cd frontend && npm install")
        sys.exit(1)


def get_npm_command() -> str:
    """
    Return the correct npm command for the current platform.
    
    Returns:
        'npm.cmd' on Windows, 'npm' on other platforms
    """
    return "npm.cmd" if sys.platform == "win32" else "npm"


def get_celery_pool() -> str:
    """
    Return the appropriate Celery pool for the current platform.
    Windows requires solo pool due to multiprocessing limitations.
    
    Returns:
        'solo' on Windows, 'prefork' on other platforms
    """
    return "solo" if sys.platform == "win32" else "prefork"


def kill_stale_ports() -> None:
    """
    Kill any processes holding ports needed by DocuForge AI.
    Prevents "Address already in use" errors on restart.
    """
    for port in [3000, 3001, 3002, 8000]:
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{port}"',
                shell=True, capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) > 0 and parts[-1].isdigit():
                        pid = parts[-1]
                        try:
                            subprocess.run(
                                f'taskkill /PID {pid} /F',
                                shell=True, capture_output=True, timeout=3
                            )
                        except Exception:
                            pass
        except Exception:
            pass
    time.sleep(1)


def main() -> None:
    """
    Launch all DocuForge AI services in order with health checks.
    Starts backend, then Celery worker, then frontend, then opens browser.
    """
    kill_stale_ports()
    signal.signal(signal.SIGINT, kill_all)
    signal.signal(signal.SIGTERM, kill_all)

    check_prerequisites()

    print("=" * 55)
    print("   DocuForge AI — Starting all services")
    print("=" * 55)

    # 1. FastAPI backend
    print("\n[1/3] Starting FastAPI backend (port 8000)...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app",
         "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=ROOT,
        env={**os.environ},
    )
    processes.append(backend)
    time.sleep(3)

    if backend.poll() is not None:
        print("ERROR: Backend failed to start.")
        print("Check your .env file has a valid GEMINI_API_KEY")
        kill_all()

    print("     ✓ Backend started")

    # 2. Celery worker
    pool = get_celery_pool()
    print(f"\n[2/3] Starting Celery worker (pool={pool})...")
    worker = subprocess.Popen(
        [sys.executable, "-m", "celery",
         "-A", "api.workers.celery_app", "worker",
         "--loglevel=info", f"--pool={pool}"],
        cwd=ROOT,
        env={**os.environ},
    )
    processes.append(worker)
    time.sleep(3)

    if worker.poll() is not None:
        print("ERROR: Celery worker failed to start.")
        print("Check your UPSTASH_REDIS_URL in .env is correct")
        kill_all()

    print("     ✓ Celery worker started")

    # 3. React frontend
    npm = get_npm_command()
    print("\n[3/3] Starting React frontend (port 3000)...")
    frontend = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=FRONTEND,
        env={**os.environ},
    )
    processes.append(frontend)
    time.sleep(4)

    if frontend.poll() is not None:
        print("ERROR: Frontend failed to start.")
        print("Run: cd frontend && npm install")
        kill_all()

    print("     ✓ Frontend started")

    # Open browser
    print("\n" + "=" * 55)
    print("   ✓ DocuForge AI is running!")
    print("")
    print("   Dashboard  →  http://localhost:3000")
    print("   API Docs   →  http://localhost:8000/docs")
    print("   Health     →  http://localhost:8000/health")
    print("")
    print("   Press Ctrl+C to stop all services")
    print("=" * 55 + "\n")

    webbrowser.open("http://localhost:3000")

    # Keep alive and monitor processes
    try:
        while True:
            time.sleep(2)
            if backend.poll() is not None:
                print("\nWARNING: Backend stopped unexpectedly")
                kill_all()
            if worker.poll() is not None:
                print("\nWARNING: Celery worker stopped unexpectedly")
                kill_all()
            if frontend.poll() is not None:
                print("\nWARNING: Frontend stopped unexpectedly")
                kill_all()
    except KeyboardInterrupt:
        kill_all()


if __name__ == "__main__":
    main()
