import socket
import threading
import logging
from logging.handlers import RotatingFileHandler
import os
import struct
import random

MYSQL_PORT = 3307
MYSQL_BANNER = b"5.7.29-0ubuntu0.18.04.1"

# Loggers
creds_logger = logging.getLogger('mysql_creds')
creds_logger.setLevel(logging.INFO)
creds_handler = RotatingFileHandler('mysql_creds.log', maxBytes=2048, backupCount=5)
creds_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
creds_logger.addHandler(creds_handler)

audits_logger = logging.getLogger('mysql_audits')
audits_logger.setLevel(logging.INFO)
audits_handler = RotatingFileHandler('mysql_audits.log', maxBytes=2048, backupCount=5)
audits_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
audits_logger.addHandler(audits_handler)

def log_credential(ip, username, password):
    creds_logger.info(f"{ip} USER={username} PASS={password}")

def log_query(ip, query):
    audits_logger.info(f"{ip} QUERY={query}")

def build_handshake_packet():
    # Based on MySQL protocol, not full but enough for login
    protocol_version = 10
    server_version = MYSQL_BANNER + b'\x00'
    thread_id = random.randint(1000, 9999)
    salt1 = os.urandom(8)
    filler = b'\x00'
    server_capabilities = 0xFFFF
    server_language = 0x21  # utf8_general_ci
    server_status = 0x0002
    salt2 = os.urandom(12)
    handshake = struct.pack(
        '<B', protocol_version
    ) + server_version + struct.pack(
        '<I', thread_id
    ) + salt1 + filler + struct.pack(
        '<H', server_capabilities
    ) + struct.pack(
        'B', server_language
    ) + struct.pack(
        '<H', server_status
    ) + b'\x00'*13 + salt2 + b'\x00'
    packet_length = len(handshake)
    header = struct.pack('<I', packet_length)[:3] + b'\x00'  # packet number 0
    return header + handshake

def build_ok_packet():
    # Minimal OK packet
    payload = b'\x00\x00\x00\x02\x00\x00\x00'
    header = struct.pack('<I', len(payload))[:3] + b'\x02'
    return header + payload

def build_err_packet():
    payload = b'\xff\x48\x04#28000Access denied for user'  # truncated
    header = struct.pack('<I', len(payload))[:3] + b'\x01'
    return header + payload

def parse_login_packet(data):
    # Not full parse, just try to extract username and password
    try:
        # Username is after 32nd byte
        user_start = 36
        user_end = data.find(b'\x00', user_start)
        username = data[user_start:user_end].decode(errors='ignore')
        # Password is after username null byte
        passwd_start = user_end + 1
        passwd_len = data[passwd_start]
        password = data[passwd_start+1:passwd_start+1+passwd_len].hex()
        return username, password
    except Exception:
        return '', ''

def handle_client(conn, addr):
    ip = addr[0]
    try:
        # Send handshake
        conn.sendall(build_handshake_packet())
        data = conn.recv(4096)
        if not data:
            return
        username, password = parse_login_packet(data)
        log_credential(ip, username, password)
        # Send OK (fake success)
        conn.sendall(build_ok_packet())
        while True:
            data = conn.recv(4096)
            if not data:
                break
            # First byte is command type, 0x03=COM_QUERY
            if data[0] == 0x03:
                try:
                    query = data[1:].decode(errors='ignore')
                except Exception:
                    query = '<decode error>'
                log_query(ip, query)
                # Respond with fake OK
                conn.sendall(build_ok_packet())
            else:
                conn.sendall(build_ok_packet())
    except Exception as e:
        audits_logger.info(f"{ip} ERROR={e}")
    finally:
        conn.close()

def start_mysql_honeypot(host='0.0.0.0', port=MYSQL_PORT):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(10)
    print(f"[*] MySQL Honeypot listening on {host}:{port}")
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
    start_mysql_honeypot()
