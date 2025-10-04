#!/usr/bin/env python3
"""
Simple HTTP server to serve the Meteor Madness frontend
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Set the directory to serve
FRONTEND_DIR = Path(__file__).parent
os.chdir(FRONTEND_DIR)

# Configure the server
PORT = 3001
Handler = http.server.SimpleHTTPRequestHandler

# Add CORS headers to allow requests to backend
class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    print(f"Serving frontend at http://localhost:{PORT}")
    print(f"Frontend directory: {FRONTEND_DIR}")
    print("Press Ctrl+C to stop the server")
    
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            sys.exit(0)
