"""Lightweight static file server for the Astroyd Meteor Madness frontend.

Run this script to serve the contents of the ``astroyd-meteor-madness-main``
folder during local development.  By default the site is hosted on
``http://localhost:3000`` but the port and bind address can be customised via
command-line arguments.
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import sys
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer


REPO_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = REPO_ROOT / "astroyd-meteor-madness-main"


class FrontendRequestHandler(SimpleHTTPRequestHandler):
    """Serve files from the frontend directory with quiet logging."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - inherited
        # SimpleHTTPRequestHandler uses ``format % args`` internally; suppressing
        # the output keeps the terminal tidy while developing.
        pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="Port to bind the development server (default: 3000)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host/IP address to bind the development server (default: 0.0.0.0)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if not FRONTEND_DIR.exists():
        print(f"Error: frontend directory '{FRONTEND_DIR}' does not exist.", file=sys.stderr)
        return 1

    args = parse_args(argv or sys.argv[1:])

    with contextlib.ExitStack() as stack:
        # Ensure the working directory is the frontend directory so that
        # relative asset paths are resolved correctly.
        stack.enter_context(contextlib.chdir(FRONTEND_DIR))

        handler = functools.partial(FrontendRequestHandler)

        # Allow address reuse to prevent "address already in use" errors when
        # restarting the server rapidly during development.
        TCPServer.allow_reuse_address = True
        with TCPServer((args.host, args.port), handler) as httpd:
            host, port = httpd.server_address
            url = f"http://{host if host != '0.0.0.0' else 'localhost'}:{port}"
            print(f"Serving Astroyd Meteor Madness frontend at {url}")
            print("Press Ctrl+C to stop.")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nStopping server...")
    return 0


if __name__ == "__main__":
    sys.exit(main())

