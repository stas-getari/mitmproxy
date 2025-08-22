import hashlib
import json
import os
from datetime import datetime, timezone

from db import clients

FILES_DIR = "/home/mitmproxyuser/Downloads/"

# Global variables set during initialization
ip_address = hostname = client = None
platforms = {
    "tinder": ["tinder"],
    "okcupid": ["okcupid"],
    "match": ["match"],
    "bumble": ["bumble"],
    "hinge": ["hinge", "sendbird"],
}


async def initialize_client_info():
    global ip_address, hostname, client
    ip_address = os.popen("hostname -I").read().strip().split(" ")[0]
    hostname = os.popen("hostname").read().strip()
    client = await clients.find_one({"vidaId": hostname})


def process_request_response(flow):
    """Extracts relevant information from the request and response."""
    request = flow.request
    response = flow.response
    request_headers = dict(request.headers)
    response_headers = dict(response.headers)
    datetime_now = datetime.now(timezone.utc)
    platform = next((k for k, v in platforms.items() if any(p in request.pretty_host for p in v)), "unknown")

    # Parse response body as JSON if possible, otherwise keep as string
    decoded_response = response.content.decode("utf-8", "replace")
    try:
        response_body = json.loads(decoded_response)
    except:
        response_body = decoded_response

    # Parse request body as JSON if possible, otherwise keep as string
    decoded_request = request.content.decode("utf-8", "replace")
    try:
        request_body = json.loads(decoded_request)
    except:
        request_body = decoded_request

    log_entry = {
        # New schema fields (matching the MongoDB structure)
        "clientId": client["_id"] if client else None,
        "url": f"{request.scheme}://{request.pretty_host}{request.path}",
        "response": response_body,
        "platform": platform,
        "method": request.method,
        "payload": request_body,
        "createdAt": datetime_now,
        "updatedAt": datetime_now,
        # Additional mitmproxy-specific fields (useful to keep)
        "server": hostname,
        "serverIp": ip_address,
        "statusCode": response.status_code,
        "reason": response.reason,
        "httpVersion": response.http_version,
        "scheme": request.scheme,
        "host": request.host,
        "site": request.pretty_host,
        "path": request.path.split("?")[0],
        "query": request.query,
        "requestHeaders": request_headers,
        "responseHeaders": response_headers,
        # "response_length": len(response_body),
        # "response_time": response.timestamp_end - response.timestamp_start,
    }

    return {k: v for k, v in log_entry.items() if v}


def save_file(flow, log_entry):
    content_type = flow.response.headers.get("Content-Type", "")
    content = flow.response.content

    if content and "image" in content_type:  # Adjust conditions as needed
        # Handle as a file, save it, and log the path in the same MongoDB document.

        # Extract or generate a filename
        file_name = flow.request.path.split("?")[0].split("/")[-1]
        if not file_name:
            # In case the URL doesn't include a filename, generate a md5 name
            file_name = hashlib.md5(content).hexdigest()

        file_path = os.path.join(FILES_DIR, file_name)

        # Save the file
        with open(file_path, "wb") as file_out:
            file_out.write(content)

        # Add file path to the log entry
        log_entry["file_path"] = file_path
        log_entry["response_body"] = None

    return log_entry


def process_websocket(flow):
    """Extracts relevant information from WebSocket messages."""
    request = flow.request
    datetime_now = datetime.now(timezone.utc)
    platform = next((k for k, v in platforms.items() if any(p in request.pretty_host for p in v)), "unknown")

    # Process WebSocket messages into serializable format
    messages_data = []
    if flow.websocket and flow.websocket.messages:
        for message in flow.websocket.messages:
            try:
                # Decode message content, similar to how request/response bodies are handled
                if isinstance(message.content, bytes):
                    decoded_content = message.content.decode("utf-8", "replace")
                else:
                    decoded_content = str(message.content)

                # Try to parse as JSON if possible, otherwise keep as string
                try:
                    message_body = json.loads(decoded_content)
                except:
                    message_body = decoded_content

                message_data = {
                    "content": message_body,
                    "direction": "outgoing" if message.from_client else "incoming",
                    "createdAt": datetime.fromtimestamp(message.timestamp, timezone.utc),
                }
                messages_data.append(message_data)
            except Exception as e:
                print(f"Error processing WebSocket message: {e}")

    log_entry = {
        # New schema fields (matching the MongoDB structure)
        "clientId": client["_id"] if client else None,
        "url": f"{request.scheme}://{request.pretty_host}{request.path}",
        "response": messages_data,  # Store messages in response field
        "platform": platform,
        "method": "WEBSOCKET",
        "payload": None,  # WebSockets don't have initial payload like HTTP
        "createdAt": datetime_now,
        "updatedAt": datetime_now,
        # Additional mitmproxy-specific fields (useful to keep)
        "server": hostname,
        "serverIp": ip_address,
        "scheme": request.scheme,
        "host": request.host,
        "site": request.pretty_host,
        "path": request.path.split("?")[0],
        "query": request.query,
        "requestHeaders": dict(request.headers),
        "messageCount": len(messages_data),
    }

    return {k: v for k, v in log_entry.items() if v}
