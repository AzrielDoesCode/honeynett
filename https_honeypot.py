import socket
import ssl
import threading
import logging
from logging.handlers import RotatingFileHandler
import datetime

# Set up logging
logger = logging.getLogger('https_honeypot')
logger.setLevel(logging.INFO)

# Set up rotating file logging
handler = RotatingFileHandler('https_creds.log', maxBytes=2000, backupCount=5)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

# Set up rotating file logging for audits
audit_handler = RotatingFileHandler('https_audits.log', maxBytes=2000, backupCount=5)
audit_handler.setLevel(logging.INFO)
logger.addHandler(audit_handler)

class HTTPSHoneypot:
    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)

        # Create self-signed certificate
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain('server.crt', 'server.key')

    def handle_connection(self, client_socket, address):
        logger.info(f'Connection from {address[0]}:{address[1]}')
        try:
            ssl_socket = self.context.wrap_socket(client_socket, server_side=True)
            request = ssl_socket.recv(1024)
            logger.info(f'Received request from {address[0]}:{address[1]}: {request}')
            response = b'HTTP/1.1 200 OK\r\n\r\nWelcome to the honeypot!'
            ssl_socket.sendall(response)
            ssl_socket.close()
        except Exception as e:
            logger.error(f'Error handling connection from {address[0]}:{address[1]}: {e}')
        finally:
            client_socket.close()

    def start(self):
        logger.info(f'Starting HTTPS honeypot on port {self.port}')
        while True:
            client_socket, address = self.server_socket.accept()
            threading.Thread(target=self.handle_connection, args=(client_socket, address)).start()

if __name__ == '__main__':
    # Generate self-signed certificate if it doesn't exist
    try:
        with open('server.crt', 'r') as f:
            pass
    except FileNotFoundError:
        import subprocess
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', 'server.key', '-out', 'server.crt', '-days', '365', '-subj', '/C=US/ST=State/L=Locality/O=Organization/CN=localhost'])

    honeypot = HTTPSHoneypot(8443)
    honeypot.start()