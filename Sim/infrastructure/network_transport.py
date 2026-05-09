import socket

class UDPTransport:
    def __init__(self, listen_port: int, send_port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", listen_port))
        self.sock.settimeout(0.02)
        self.send_port = send_port

    def receive(self):
        try:
            data, addr = self.sock.recvfrom(4096)
            return data.decode(), addr
        except socket.timeout:
            return None, None
        except Exception:
            return None, None

    def send(self, data: bytes, target_ip: str):
        self.sock.sendto(data, (target_ip, self.send_port))