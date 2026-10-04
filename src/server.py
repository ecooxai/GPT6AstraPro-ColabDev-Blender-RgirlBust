from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parent.parent / "preview"
class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,".glb":"model/gltf-binary",".blend":"application/octet-stream",".js":"text/javascript"}
    def __init__(self,*args,**kw): super().__init__(*args,directory=str(ROOT),**kw)
    def end_headers(self):
        self.send_header("Cache-Control","no-cache")
        self.send_header("X-Content-Type-Options","nosniff")
        super().end_headers()
ThreadingHTTPServer(("0.0.0.0",4326),Handler).serve_forever()
