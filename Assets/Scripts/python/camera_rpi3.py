import io
import logging
import socketserver
from threading import Condition, Thread
from http import server
from picamera2 import Picamera2

# --- CONFIGURATION PAGE WEB ---
PAGE="""\
<html>
<head>
<title>Cogni-Robot - Vision System</title>
</head>
<body>
<center><h1>Cogni-Robot - Vision Live</h1></center>
<center><img src="stream.mjpg" width="640" height="480"></center>
<p><center>Point d'accès Unity : <b>/snapshot.jpg</b></center></p>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Accueil
        if self.path == '/' or self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)

        # 2. ENDPOINT SNAPSHOT (Pour ton code Unity actuel)
        elif self.path == '/snapshot.jpg':
            with output.condition:
                output.condition.wait() # Attend une nouvelle frame
                frame = output.frame
            self.send_response(200)
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', len(frame))
            self.end_headers()
            self.wfile.write(frame)

        # 3. ENDPOINT STREAM MJPEG (Conservé pour debug/navigateur)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning('Client MJPEG déconnecté : %s', str(e))
        
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

# --- LOGIQUE DE CAPTURE ---
def capture_frames(picam2, output):
    while True:
        try:
            # Capture une image à chaque itération
            img = picam2.capture_image()
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            
            with output.condition:
                output.frame = buf.getvalue()
                # Réveille tous les clients (Unity ou Web)
                output.condition.notify_all()
        except Exception as e:
            logging.warning('Erreur lors de la capture : %s', str(e))
            break

# --- DÉMARRAGE ---
output = StreamingOutput()

# Initialisation de la caméra
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

# Lancement du thread de capture
capture_thread = Thread(target=capture_frames, args=(picam2, output))
capture_thread.daemon = True
capture_thread.start()

# Lancement du serveur
try:
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    print("--- SERVEUR COGNI-VISION ACTIF ---")
    print("Web UI  : http://localhost:8000")
    print("Unity   : http://localhost:8000/snapshot.jpg")
    server.serve_forever()
finally:
    picam2.stop()
