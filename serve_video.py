"""Simple HTTP server with video page + optional ngrok tunnel."""
import http.server
import threading
import os

PORT = 8080
VIDEO_FILE = "atmospheric_output.mp4"

HTML = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Atmospheric Video</title>
  <style>
    body {{ margin: 0; background: #000; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
    video {{ max-width: 100%; max-height: 100vh; }}
  </style>
</head>
<body>
  <video controls autoplay loop playsinline>
    <source src="/{VIDEO_FILE}" type="video/mp4">
  </video>
</body>
</html>
"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode())
        else:
            super().do_GET()
    def log_message(self, format, *args):
        pass  # suppress logs

os.chdir("/home/user/-")
server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
print(f"Local: http://localhost:{PORT}")

try:
    from pyngrok import ngrok
    public_url = ngrok.connect(PORT, bind_tls=True)
    print(f"\nスマホでこのURLを開いてください:\n{public_url}\n")
    print("終了するには Ctrl+C を押してください")
    ngrok.get_ngrok_process().proc.wait()
except Exception as e:
    print(f"ngrok not available ({e})")
    print(f"同じWi-Fiなら http://<このPCのIP>:{PORT} でアクセスしてください")
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
