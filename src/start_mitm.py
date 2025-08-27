#!/usr/bin/env python3
import asyncio
import os

import utils


def parse_proxy_config(proxy: str):
    # Expected exact format: host:port@username:password
    if proxy:
        host_port, creds = proxy.split("@", 1)
        host, port = host_port.split(":", 1)
        username, password = creds.split(":", 1)
    else:
        host = port = username = password = None

    return host, port, username, password


async def main():
    print("Starting mitmproxy initialization...", flush=True)

    # Initialize and wait until client doc is available
    print("Waiting for client info to be available...", flush=True)
    while True:
        await utils.initialize_client_info()
        if utils.client:
            print("Client info successfully loaded", flush=True)
            break
        print("Client info not ready, waiting 1 second...", flush=True)
        await asyncio.sleep(1)

    # Parse proxy config from client settings
    host = port = username = password = None
    if static_proxy := utils.client["settings"].get("staticProxy"):
        print(f"Static proxy setting: {static_proxy}", flush=True)
        host, port, username, password = parse_proxy_config(static_proxy)
    elif dynamic_proxy := utils.client["settings"].get("dynamicProxy"):
        print(f"Dynamic proxy setting: {dynamic_proxy}", flush=True)
        host, port, username, password = parse_proxy_config(dynamic_proxy)

    # fmt: off
    if host and port and username and password:
        print("Configuring upstream proxy mode...", flush=True)
        cmd = [
            "mitmdump",
            "--mode", f"upstream:http://{host}:{port}",
            "--upstream-auth", f"{username}:{password}",
            "--set", "confdir=/home/mitmproxy/.mitmproxy",
            "--showhost",
            "--scripts", "logs_to_mongodb.py",
        ]
    else:
        print("Configuring transparent proxy mode...", flush=True)
        cmd = [
            "mitmdump",
            "--mode", "transparent",
            "--set", "confdir=/home/mitmproxy/.mitmproxy",
            "--showhost",
            "--scripts", "logs_to_mongodb.py",
        ]

    print(f"Executing command: {' '.join(cmd)}", flush=True)
    print("Starting mitmdump process...", flush=True)
    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    asyncio.run(main())
