#!/usr/bin/env python3
import asyncio
import os
from bson import ObjectId

from db import clients, proxies


def parse_proxy_config(proxy: str):
    # Expected exact format: host:port@username:password
    if proxy:
        host_port, creds = proxy.split("@", 1)
        host, port = host_port.split(":", 1)
        username, password = creds.split(":", 1)
    else:
        host = port = username = password = None

    return host, port, username, password


async def get_proxy_from_object_id(proxy_id: ObjectId):
    """Fetch proxy configuration from MongoDB using objectId."""
    try:
        if proxy_doc := await proxies.find_one({"_id": proxy_id}):
            return {
                "host": proxy_doc["proxyAddress"],
                "port": proxy_doc["port"],
                "username": proxy_doc["username"],
                "password": proxy_doc["password"]
            }
    except Exception as e:
        print(f"Error fetching proxy from MongoDB: {e}", flush=True)
    return None


async def get_proxy_config(proxy_setting):
    """Get proxy configuration from either string format or MongoDB objectId."""
    if not proxy_setting:
        return None

    # Check if it's a string format (host:port@username:password)
    if isinstance(proxy_setting, str) and "@" in proxy_setting and ":" in proxy_setting:
        host, port, username, password = parse_proxy_config(proxy_setting)
        return { "host": host, "port": port, "username": username, "password": password}

    # Check if it's an ObjectId object
    elif isinstance(proxy_setting, ObjectId):
        return await get_proxy_from_object_id(proxy_setting)

    return None


async def main():
    print("Starting mitmproxy initialization...", flush=True)

    # Parse proxy config from client settings
    client = await clients.find_one({"vidaId": os.popen("hostname").read().strip().replace("-auto-web", "")})
    if not client:
        print("Client not found", flush=True)
        return

    proxy_config = None
    if proxy_setting := client["settings"].get("proxy"):
        print(f"Proxy setting: {proxy_setting}", flush=True)
        proxy_config = await get_proxy_config(proxy_setting)
        if proxy_config:
            print(f"Proxy config loaded: {proxy_config['host']}:{proxy_config['port']}", flush=True)
        else:
            print("Failed to load proxy configuration", flush=True)

    # fmt: off
    if proxy_config:
        print("Configuring upstream proxy mode...", flush=True)
        cmd = [
            "mitmdump",
            "--mode", f"upstream:http://{proxy_config['host']}:{proxy_config['port']}",
            "--upstream-auth", f"{proxy_config['username']}:{proxy_config['password']}",
            "--set", "confdir=/home/mitmproxy/.mitmproxy",
            "--showhost",
            "--scripts", "logs_to_mongodb.py",
        ]
    else:
        print("No proxy config found, waiting for 1 minute before retrying...", flush=True)
        await asyncio.sleep(60)
        return await main()

    print(f"Executing command: {' '.join(cmd)}", flush=True)
    print("Starting mitmdump process...", flush=True)
    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    asyncio.run(main())
