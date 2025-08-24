#!/usr/bin/env python3
import asyncio
import os

import utils


def parse_static_proxy(static_proxy: str):
    # Expected exact format: host:port@username:password
    if static_proxy:
        host_port, creds = static_proxy.split("@", 1)
        host, port = host_port.split(":", 1)
        username, password = creds.split(":", 1)
    else:
        host = port = username = password = None

    return host, port, username, password


async def main():
    # Initialize and wait until client doc is available
    while True:
        await utils.initialize_client_info()
        if utils.client:
            break
        await asyncio.sleep(1)

    static_proxy = utils.client["settings"].get("staticProxy")

    host, port, username, password = parse_static_proxy(static_proxy)

    # fmt: off
    if host and port:
        cmd = [
            "mitmdump",
            "--mode", f"upstream:http://{host}:{port}",
            "--upstream-auth", f"{username}:{password}",
            "--set", "confdir=/home/mitmproxy/.mitmproxy",
            "--showhost",
            "--scripts", "logs_to_mongodb.py",
        ]
    else:
        cmd = [
            "mitmdump",
            "--mode", "transparent",
            "--set", "confdir=/home/mitmproxy/.mitmproxy",
            "--showhost",
            "--scripts", "logs_to_mongodb.py",
        ]

    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    asyncio.run(main())
