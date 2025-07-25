#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WEB TRAFFIC BOT - SOCKS & HTTP/HTTPS Proxy Support (Python 3)
"""

import urllib.request
import urllib.error
import sys
import time
import random
import socks
import socket
import datetime
import json
import os
import argparse

# === Argument Parser ===
parser = argparse.ArgumentParser(description="Web Traffic Bot with Proxy Support")

parser.add_argument('--proxylist', help='Path to your Proxylist file')
parser.add_argument('--urls', help='Path to file with list of URLs (one per line)')
parser.add_argument('--loops', type=int, help='How many times to loop through the full proxy list')
parser.add_argument('--wait', type=float, help='How many seconds to wait between each proxy request')
parser.add_argument('--logformat', choices=['txt', 'json'], help='Save success logs as txt or json')

args = parser.parse_args()

print("""
######################################################################
#--> Web Traffic Bot 0.0.3                                        <--#
#--> by BORG                                                      <--#                              
######################################################################
""")

# === Input Fallbacks if CLI args are missing ===

url_file_path = args.urls or input("--> Path to file with URLs to visit: ").strip()
proxylisttext = args.proxylist or input("--> Path to your Proxylist file: ").strip()
link_invation = args.urls or input("--> Link to Autovisit (Full URL with http:// or https://): ").strip()

# Load URL list
try:
    with open(url_file_path, "r") as url_file:
        url_list = [line.strip() for line in url_file if line.strip()]
except FileNotFoundError:
    print(f"[-] URL list file not found: {url_file_path}")
    sys.exit(1)
try:
    loop_count = args.loops if args.loops is not None else int(input("--> How many times to loop through the full proxy list? "))
    wait_seconds = args.wait if args.wait is not None else float(input("--> How many seconds to wait between each proxy request? "))
except ValueError:
    print("[-] Invalid input. Please enter numbers only.")
    sys.exit(1)

log_format = args.logformat or input("--> Save success logs as TXT or JSON? (txt/json): ").strip().lower()
if log_format not in ["txt", "json"]:
    print("[-] Invalid format. Please choose 'txt' or 'json'.")
    sys.exit(1)

success_log_path = "success_proxies.txt" if log_format == "txt" else "success_proxies.json"

# === User Agents and Referers ===
useragents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Mozilla/5.0 (X11; Linux x86_64)',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
]

referers = [
    'http://google.com', 'http://bing.com', 'http://facebook.com',
    'http://twitter.com', 'http://youtube.com', 'http://instagram.com',
]

# === Core Bot Function (Updated) ===
def bot(proxy_address):
    proxy = proxy_address.strip()

    if proxy.startswith("socks5://"):
        proxy_type = socks.SOCKS5
        proxy = proxy[9:]
    elif proxy.startswith("socks4://"):
        proxy_type = socks.SOCKS4
        proxy = proxy[9:]
    elif proxy.startswith("http://") or proxy.startswith("https://"):
        proxy_type = "http"
        proxy = proxy.split("://")[1]
    else:
        proxy_type = "http"

    ip_port = proxy.split(":")
    if len(ip_port) != 2:
        print(f"[!] Invalid proxy format: {proxy_address}")
        return

    ip, port = ip_port[0], int(ip_port[1])

    try:
        if proxy_type in [socks.SOCKS4, socks.SOCKS5]:
            socks.set_default_proxy(proxy_type, ip, port)
            socket.socket = socks.socksocket
            opener = urllib.request.build_opener()
        else:
            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://{ip}:{port}",
                "https": f"http://{ip}:{port}"
            })
            opener = urllib.request.build_opener(proxy_handler)

        opener.addheaders = [
            ('User-agent', random.choice(useragents)),
            ('Referer', random.choice(referers))
        ]
        urllib.request.install_opener(opener)

        for target_url in url_list:
            try:
                print(f"[*] Visiting {target_url} using proxy: {proxy_address}")
                with urllib.request.urlopen(target_url, timeout=20) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    if target_url in content:
                        print(f"[+] Success: {proxy_address} -> {target_url}")
                        timestamp = datetime.datetime.now().isoformat()
                        log_entry = {
                            "proxy": proxy_address,
                            "url": target_url,
                            "timestamp": timestamp
                        }

                        if log_format == "txt":
                            with open(success_log_path, "a") as f:
                                f.write(f"[{timestamp}] {proxy_address} -> {target_url}\n")
                        elif log_format == "json":
                            if os.path.exists(success_log_path):
                                with open(success_log_path, "r") as f:
                                    try:
                                        existing_logs = json.load(f)
                                    except json.JSONDecodeError:
                                        existing_logs = []
                            else:
                                existing_logs = []

                            existing_logs.append(log_entry)
                            with open(success_log_path, "w") as f:
                                json.dump(existing_logs, f, indent=4)
                    else:
                        print(f"[-] No match found for {target_url}")
            except Exception as e:
                print(f"[!] Error visiting {target_url}: {e}")

    except Exception as e:
        print(f"[!] Proxy setup failed: {e}")

# === Load and Visit ===
def load_proxies(loop_num):
    try:
        with open(proxylisttext, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
        for index, proxy in enumerate(proxies, 1):
            print(f"\n[Loop {loop_num}] Visiting with proxy #{index}: {proxy}")
            bot(proxy)
            print(f"[*] Waiting {wait_seconds} seconds before the next proxy...")
            time.sleep(wait_seconds)
    except FileNotFoundError:
        print("[-] Proxy list file not found.")
        sys.exit(1)

# === Main Entry ===
def main():
    for i in range(1, loop_count + 1):
        print(f"\n========== Starting Loop {i} of {loop_count} ==========\n")
        load_proxies(i)

if __name__ == '__main__':
    main()
