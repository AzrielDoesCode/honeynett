import socket
import threading
import logging
from logging.handlers import RotatingFileHandler
import sys

FTP_BANNER = "220 Welcome to FakeFTP Server\r\n"
FAKE_FILE_LIST = "drwxr-xr-x 2 user group 4096 Jul 15 13:14 pub\r\n-rw-r--r-- 1 user group 1234 Jul 15 13:14 readme.txt\r\n"

# Setup loggers
creds_logger = logging.getLogger('ftp_creds')
creds_logger.setLevel(logging.INFO)
creds_handler = RotatingFileHandler('ftp_creds.log', maxBytes=50000, backupCount=3)
creds_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
creds_logger.addHandler(creds_handler)

audits_logger = logging.getLogger('ftp_audits')
audits_logger.setLevel(logging.INFO)
audits_handler = RotatingFileHandler('ftp_audits.log', maxBytes=50000, backupCount=3)
audits_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
audits_logger.addHandler(audits_handler)

def log_credential(ip, username, password):
    creds_logger.info(f"{ip} USER={username} PASS={password}")

def log_command(ip, cmd):
    audits_logger.info(f"{ip} CMD={cmd}")

def handle_client(conn, addr):
    ip = addr[0]
    try:
        conn.sendall(FTP_BANNER.encode())
        username = None
        password = None
        while True:
            data = conn.recv(1024)
            if not data:
                break
            cmd_line = data.decode(errors='ignore').strip()
            if not cmd_line:
                continue
            cmd = cmd_line.split(' ')[0].upper()
            log_command(ip, cmd_line)
            if cmd == 'USER':
                username = cmd_line[5:].strip()
                conn.sendall(b"331 Username OK, need password.\r\n")
            elif cmd == 'PASS':
                password = cmd_line[5:].strip()
                log_credential(ip, username or '', password)
                conn.sendall(b"230 Login successful.\r\n")
            elif cmd == 'LIST':
                conn.sendall(b"150 Here comes the directory listing.\r\n")
                conn.sendall(FAKE_FILE_LIST.encode())
                conn.sendall(b"226 Directory send OK.\r\n")
            elif cmd == 'RETR':
                conn.sendall(b"550 File not found.\r\n")
            elif cmd == 'QUIT':
                conn.sendall(b"221 Goodbye.\r\n")
                break
            else:
                conn.sendall(b"502 Command not implemented.\r\n")
    except Exception as e:
        audits_logger.info(f"{ip} ERROR={e}")
    finally:
        conn.close()

def start_ftp_honeypot(host='0.0.0.0', port=2121):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(10)
    print(f"[*] FTP Honeypot listening on {host}:{port}")
    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[*] Shutting down honeypot.")
    finally:
        server.close()

if __name__ == '__main__':
    start_ftp_honeypot()
