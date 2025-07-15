#!/bin/bash

# Honeypot ports
PORTS=(2223 3306 21 443 8080)

function enable_firewall() {
    echo "[+] Enabling firewall..."
    sudo firewall-cmd --permanent --set-default-zone=public
    sudo systemctl start firewalld
    sudo firewall-cmd --reload
    echo "[✓] Firewall enabled."
}

function disable_firewall() {
    echo "[!] Disabling firewall..."
    sudo systemctl stop firewalld
    echo "[✓] Firewall disabled."
}

function allow_honeypot_ports() {
    echo "[+] Allowing honeypot ports..."
    for port in "${PORTS[@]}"; do
        sudo firewall-cmd --permanent --add-port=${port}/tcp
    done
    sudo firewall-cmd --reload
    echo "[✓] Honeypot ports allowed."
}

function block_honeypot_ports() {
    echo "[!] Blocking honeypot ports..."
    for port in "${PORTS[@]}"; do
        sudo firewall-cmd --permanent --remove-port=${port}/tcp
    done
    sudo firewall-cmd --reload
    echo "[✓] Honeypot ports blocked."
}

# Menu
while true; do
    echo ""
    echo "=== Honeynet Firewall Control ==="
    echo "1) Enable Firewall"
    echo "2) Disable Firewall"
    echo "3) Allow Honeypot Ports"
    echo "4) Block Honeypot Ports"
    echo "5) Exit"
    read -p "Select an option [1-5]: " opt

    case $opt in
        1) enable_firewall ;;
        2) disable_firewall ;;
        3) allow_honeypot_ports ;;
        4) block_honeypot_ports ;;
        5) echo "Bye!"; exit 0 ;;
        *) echo "Invalid option. Try again." ;;
    esac
done
