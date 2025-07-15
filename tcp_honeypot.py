import socket
import threading
import logging
from logging.handlers import RotatingFileHandler

# Set up logging
logger = logging.getLogger('tcp_honeypot')
logger.setLevel(logging.INFO)

# Set up rotating file logging
handler = RotatingFileHandler('tcp_creds.log', maxBytes=2000, backupCount=5)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

# Set up rotating file logging for audits
audit_handler = RotatingFileHandler('tcp_audits.log', maxBytes=2000, backupCount=5)
audit_handler.setLevel(logging.INFO)
logger.addHandler(audit_handler)

class TCPHoneypot:
    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)

    def handle_connection(self, client_socket, address):
        logger.info(f'Connection from {address[0]}:{address[1]}')
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                logger.info(f'Received data from {address[0]}:{address[1]}: {data}')
                client_socket.sendall(b'Welcome to the honeypot!\r\n')
                client_socket.sendall(b'Enter your credentials: ')
                credentials = client_socket.recv(1024)
                logger.info(f'Received credentials from {address[0]}:{address[1]}: {credentials}')
                with open('tcp_creds.log', 'a') as f:
                    f.write(f'{address[0]}:{address[1]} - {credentials}\n')
        except Exception as e:
            logger.error(f'Error handling connection from {address[0]}:{address[1]}: {e}')
        finally:
            client_socket.close()

    def start(self):
        logger.info(f'Starting TCP honeypot on port {self.port}')
        while True:
            client_socket, address = self.server_socket.accept()
            threading.Thread(target=self.handle_connection, args=(client_socket, address)).start()

if __name__ == '__main__':
    honeypot = TCPHoneypot(4444)
    honeypot.start()