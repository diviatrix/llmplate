#!/usr/bin/env python3
"""
Simple HTTP server for serving frontend mocks with navigation menu
Works well in Termux environment
"""

import os
import sys
import http.server
import socketserver
import webbrowser
from urllib.parse import urlparse
import socket

PORT = 8080

NAVIGATION_MENU = """
<style>
    .mock-nav {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #1a1a1a;
        padding: 15px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 20px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }}
    .mock-nav-title {{
        color: #4CAF50;
        font-size: 20px;
        font-weight: bold;
        margin-right: 20px;
    }}
    .mock-nav-links {{
        display: flex;
        gap: 15px;
        flex-wrap: wrap;
    }}
    .mock-nav-link {{
        color: #fff;
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 4px;
        transition: all 0.3s;
        font-size: 14px;
    }}
    .mock-nav-link:hover {{
        background: #4CAF50;
        color: white;
    }}
    .mock-nav-link.active {{
        background: #4CAF50;
        color: white;
    }}
    .mock-nav-info {{
        margin-left: auto;
        color: #999;
        font-size: 12px;
    }}
    body {{
        padding-top: 70px !important;
    }}
</style>
<div class="mock-nav">
    <div class="mock-nav-title">🚀 LLMplate Mocks</div>
    <div class="mock-nav-links">
        <a href="/" class="mock-nav-link">📋 Index</a>
        <a href="/auth-pages.html" class="mock-nav-link">🔐 Auth</a>
        <a href="/simple-interface.html" class="mock-nav-link">✨ Simple UI</a>
        <a href="/engineer-interface.html" class="mock-nav-link">🔧 Engineer UI</a>
        <a href="/teacher-simple-ui.html" class="mock-nav-link">👩‍🏫 Teacher Case</a>
        <a href="/hr-simple-ui.html" class="mock-nav-link">👔 HR Case</a>
    </div>
    <div class="mock-nav-info">Serving on port {port}</div>
</div>
<script>
    // Highlight active page
    const currentPath = window.location.pathname;
    document.querySelectorAll('.mock-nav-link').forEach(link => {{
        if (link.getAttribute('href') === currentPath || 
            (currentPath === '/' && link.getAttribute('href') === '/')) {{
            link.classList.add('active');
        }}
    }});
</script>
"""

class MockHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=".", **kwargs)
    
    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Redirect root to index.html
        if path == '/':
            path = '/index.html'
        
        # Check if file exists
        file_path = '.' + path
        if os.path.exists(file_path) and file_path.endswith('.html'):
            # Read the original HTML file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Inject navigation menu and feature status script before closing body tag
            nav_menu = NAVIGATION_MENU.format(port=PORT)
            feature_script = '<script src="/feature-status.js"></script>'
            content = content.replace('</body>', feature_script + nav_menu + '</body>')
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-Length', len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        else:
            # Use default handler for non-HTML files
            super().do_GET()
    
    def log_message(self, format, *args):
        # Custom log format
        print(f"[{self.log_date_time_string()}] {format % args}")

def get_local_ip():
    """Get local IP address"""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    # Change to frontend-mocks directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Find available port
    global PORT
    for port in range(8080, 8090):
        try:
            with socketserver.TCPServer(("", port), MockHTTPRequestHandler) as httpd:
                PORT = port
                break
        except OSError:
            continue
    
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print("🚀 LLMplate Frontend Mocks Server")
    print("="*60)
    print(f"\n📡 Server running on:")
    print(f"   Local:    http://localhost:{PORT}")
    print(f"   Network:  http://{local_ip}:{PORT}")
    print(f"\n📁 Serving from: {script_dir}")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # Try to open browser (may not work in Termux)
    if sys.platform != "linux" or "TERMUX" not in os.environ.get("PREFIX", ""):
        try:
            webbrowser.open(f'http://localhost:{PORT}')
        except:
            pass
    
    try:
        with socketserver.TCPServer(("", PORT), MockHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()