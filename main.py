"""
Memorize Master Entrypoint & Orchestrator
Provides unified commands to run:
  - Both Backend & Frontend simultaneously (python main.py / python main.py start)
  - FastAPI REST API & Universal FastMCP Server (python main.py backend / python main.py server)
  - Vite React Frontend Web Application (python main.py frontend / python main.py ui)
  - FastMCP Server for Claude/Cursor/Gemini (python main.py mcp / python main.py --transport stdio)
  - Interactive Terminal CLI (python main.py cli)
"""

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from mcp import run_mcp_server
from mcp.config import DEFAULT_PORT, DEFAULT_TRANSPORT, SERVER_NAME
import cli

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"


def print_banner(backend_port: int, frontend_port: int, host: str = "localhost"):
    """Prints a styled startup banner with accessible service links."""
    display_host = "localhost" if host in ("0.0.0.0", "127.0.0.1", "") else host
    print("\033[1;36m" + "=" * 70 + "\033[0m")
    print(f"\033[1;32m  🧠 MEMORIZE KNOWLEDGE BASE — FULL STACK ACTIVE\033[0m")
    print("\033[1;36m" + "=" * 70 + "\033[0m")
    print(f"  \033[1;35m🌐 Frontend Web UI:\033[0m        http://{display_host}:{frontend_port}")
    print(f"  \033[1;34m⚙️  Backend REST API:\033[0m       http://{display_host}:{backend_port}")
    print(f"  \033[1;33m📚 Interactive API Docs:\033[0m   http://{display_host}:{backend_port}/docs")
    print(f"  \033[1;32m🤖 Universal MCP SSE:\033[0m      http://{display_host}:{backend_port}/sse")
    print(f"  \033[1;36m⚡ Universal MCP HTTP:\033[0m     http://{display_host}:{backend_port}/mcp")
    print("\033[1;36m" + "=" * 70 + "\033[0m")
    print("  \033[90mPress Ctrl+C to terminate all services.\033[0m")
    print("\033[1;36m" + "=" * 70 + "\033[0m\n")


def stream_process_output(process: subprocess.Popen, prefix: str, color_code: str):
    """Streams stdout/stderr of a child process with a colored prefix tag."""
    try:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            stripped = line.rstrip()
            if stripped:
                print(f"{color_code}[{prefix}]\033[0m {stripped}")
    except (ValueError, Exception):
        pass


def run_backend(host: str = "0.0.0.0", port: int = DEFAULT_PORT, reload: bool = True):
    """Runs the FastAPI REST and Universal FastMCP backend server."""
    import uvicorn

    display_host = "localhost" if host in ("0.0.0.0", "127.0.0.1", "") else host
    print(f"\033[1;34m[backend]\033[0m Starting FastAPI REST & MCP Server on http://{display_host}:{port}")
    print(f"\033[1;34m[backend]\033[0m Swagger UI Docs: http://{display_host}:{port}/docs")
    print(f"\033[1;34m[backend]\033[0m FastMCP Endpoints: http://{display_host}:{port}/sse & http://{display_host}:{port}/mcp")
    uvicorn.run("api.server:app", host=host, port=port, reload=reload)


def run_frontend(host: str = "0.0.0.0", frontend_port: int = 8888, backend_port: int = DEFAULT_PORT):
    """Runs the Vite React frontend development server."""
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("\033[1;33m[frontend]\033[0m node_modules not found. Installing frontend dependencies (npm install)...")
        subprocess.run(["npm", "install"], cwd=str(FRONTEND_DIR), check=True)

    env = os.environ.copy()
    env["FRONTEND_PORT"] = str(frontend_port)
    env["BACKEND_PORT"] = str(backend_port)
    env["PORT"] = str(frontend_port)

    display_host = "localhost" if host in ("0.0.0.0", "127.0.0.1", "") else host
    print(f"\033[1;35m[frontend]\033[0m Starting Vite Dev Server on http://{display_host}:{frontend_port}")
    print(f"\033[1;35m[frontend]\033[0m Proxying /api requests to backend on port {backend_port}")

    cmd = ["npm", "run", "dev", "--", "--port", str(frontend_port), "--host", host]
    subprocess.run(cmd, cwd=str(FRONTEND_DIR), env=env)


def run_all(host: str = "0.0.0.0", backend_port: int = DEFAULT_PORT, frontend_port: int = 8888, reload: bool = True):
    """Concurrently runs both FastAPI backend and Vite frontend with unified logging and graceful shutdown."""
    node_modules = FRONTEND_DIR / "node_modules"
    if not node_modules.exists():
        print("\033[1;33m[setup]\033[0m Installing frontend dependencies (npm install)...")
        subprocess.run(["npm", "install"], cwd=str(FRONTEND_DIR), check=True)

    env = os.environ.copy()
    env["FRONTEND_PORT"] = str(frontend_port)
    env["BACKEND_PORT"] = str(backend_port)
    env["PORT"] = str(frontend_port)

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "api.server:app",
        "--host",
        host,
        "--port",
        str(backend_port),
    ]
    if reload:
        backend_cmd.append("--reload")

    frontend_cmd = [
        "npm",
        "run",
        "dev",
        "--",
        "--port",
        str(frontend_port),
        "--host",
        host,
    ]

    print_banner(backend_port=backend_port, frontend_port=frontend_port, host=host)

    backend_proc = subprocess.Popen(
        backend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=str(ROOT_DIR),
        env=env,
    )

    frontend_proc = subprocess.Popen(
        frontend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=str(FRONTEND_DIR),
        env=env,
    )

    t_backend = threading.Thread(
        target=stream_process_output,
        args=(backend_proc, "backend", "\033[1;34m"),
        daemon=True,
    )
    t_frontend = threading.Thread(
        target=stream_process_output,
        args=(frontend_proc, "frontend", "\033[1;35m"),
        daemon=True,
    )

    t_backend.start()
    t_frontend.start()

    shutdown_event = threading.Event()

    def handle_shutdown(signum, frame):
        if not shutdown_event.is_set():
            shutdown_event.set()
            print("\n\033[1;33m[shutdown]\033[0m Shutting down all servers...")
            for proc, name in [(backend_proc, "backend"), (frontend_proc, "frontend")]:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                except Exception:
                    pass

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        while not shutdown_event.is_set():
            b_ret = backend_proc.poll()
            f_ret = frontend_proc.poll()
            if b_ret is not None and not shutdown_event.is_set():
                print(f"\033[1;31m[backend]\033[0m Process exited with code {b_ret}")
                handle_shutdown(None, None)
                break
            if f_ret is not None and not shutdown_event.is_set():
                print(f"\033[1;31m[frontend]\033[0m Process exited with code {f_ret}")
                handle_shutdown(None, None)
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        handle_shutdown(None, None)
    finally:
        # Ensure cleanup
        for proc in (backend_proc, frontend_proc):
            try:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=2)
            except Exception:
                pass
        print("\033[1;32m[shutdown]\033[0m All servers stopped cleanly.")


def main():
    # 1. Handle legacy CLI subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        sys.argv.pop(1)
        cli.main()
        return

    # 2. Setup master argument parser
    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Memorize Knowledge Base — Master Server & Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  start, dev, all, both      Concurrently start both FastAPI backend & Vite frontend (Default in terminal)
  backend, server, api       Start only the FastAPI REST API & Universal MCP server
  frontend, ui, web          Start only the Vite frontend web application
  mcp                        Start FastMCP server (stdio / sse / streamable-http)
  cli                        Launch interactive memory manager terminal CLI

Examples:
  python main.py                     # Starts full stack (backend + frontend)
  python main.py backend             # Starts backend on http://localhost:7777
  python main.py frontend            # Starts frontend on http://localhost:8888
  python main.py mcp                 # Runs FastMCP on stdio for Claude/Cursor/IDE
  python main.py --port 8000         # Runs backend on custom port 8000
        """,
    )

    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        choices=[
            "start",
            "dev",
            "all",
            "both",
            "app",
            "backend",
            "server",
            "api",
            "frontend",
            "ui",
            "web",
            "mcp",
            "cli",
        ],
        help="Command to execute (default: start full stack in terminal, or stdio MCP when piped)",
    )

    # General & Server Options
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"Backend REST/MCP port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=8888,
        help="Frontend Vite port (default: 8888)",
    )
    parser.add_argument(
        "--reload",
        dest="reload",
        action="store_true",
        default=True,
        help="Enable auto-reload on code changes (default: True)",
    )
    parser.add_argument(
        "--no-reload",
        dest="reload",
        action="store_false",
        help="Disable auto-reload",
    )

    # FastMCP Specific Options
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=DEFAULT_TRANSPORT,
        help=f"FastMCP Transport protocol (default: {DEFAULT_TRANSPORT})",
    )

    # Flag aliases for quick execution
    parser.add_argument("--backend", "--server", "--api", dest="mode_backend", action="store_true", help="Start backend only")
    parser.add_argument("--frontend", "--ui", "--web", dest="mode_frontend", action="store_true", help="Start frontend only")
    parser.add_argument("--all", "--both", "--dev", dest="mode_all", action="store_true", help="Start both backend and frontend")

    args, extra_args = parser.parse_known_args()

    # Determine command mode
    cmd = args.command

    # If flags were used instead of positional command
    if args.mode_backend:
        cmd = "backend"
    elif args.mode_frontend:
        cmd = "frontend"
    elif args.mode_all:
        cmd = "start"

    # Default behavior when no positional command or flag is provided:
    if cmd is None:
        # If piped/redirected without a TTY (Claude Desktop, Cursor, Antigravity IDE stdio MCP)
        # OR if transport was explicitly specified as something other than default
        if not sys.stdin.isatty() or "--transport" in sys.argv:
            cmd = "mcp"
        else:
            # Interactive terminal default: start full stack
            cmd = "start"

    # Execute selected mode
    if cmd in ("start", "dev", "all", "both", "app"):
        run_all(
            host=args.host,
            backend_port=args.port,
            frontend_port=args.frontend_port,
            reload=args.reload,
        )
    elif cmd in ("backend", "server", "api"):
        run_backend(
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    elif cmd in ("frontend", "ui", "web"):
        run_frontend(
            host=args.host,
            frontend_port=args.frontend_port,
            backend_port=args.port,
        )
    elif cmd == "mcp":
        run_mcp_server(
            transport=args.transport,
            host=args.host,
            port=args.port,
        )
    elif cmd == "cli":
        cli.main()


if __name__ == "__main__":
    main()
