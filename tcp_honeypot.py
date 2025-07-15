import socket
import threading
import logging
from logging.handlers import RotatingFileHandler

# Set up logging
logger = logging.getLogger('tcp_honeypot')
logger.setLevel(logging.INFO)

# Unified rotating log handler (10MB, 5 backups)
handler = RotatingFileHandler('tcp_audits.log', maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logger.addHandler(handler)

class TCPHoneypot:
    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)

    def handle_connection(self, client_socket, address):
        ip, port = address
        logger.info(f'[+] Connection from {ip}:{port}')
        try:
            client_socket.sendall(b'Welcome to the honeypot!\r\nEnter credentials: ')
            creds = client_socket.recv(1024).decode(errors='ignore').strip()
            logger.info(f'[!] Credentials from {ip}:{port} — {creds}')
        except Exception as e:
            logger.error(f'[!] Error with {ip}:{port} — {e}')
        finally:
            client_socket.close()

    def start(self):
        logger.info(f'[*] TCP honeypot listening on port {self.port}')
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(
                    target=self.handle_connection,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
        except KeyboardInterrupt:
            logger.info("[!] Honeypot interrupted and shutting down...")
            self.server_socket.close()

if __name__ == '__main__':
    honeypot = TCPHoneypot(4444)
    honeypot.start()
