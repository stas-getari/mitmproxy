import json
import os
from datetime import datetime


FILES_DIR = "/home/mitmproxyuser/Downloads/"


def process_request_response(flow):
    """Extracts relevant information from the request and response."""
    request = flow.request
    response = flow.response
    request_headers = dict(request.headers)
    response_headers = dict(response.headers)

    try:    request_body = json.loads(request.content)
    except: request_body = request.content.decode('utf-8', 'replace')
    
    try:    response_body = json.loads(response.content)
    except: response_body = response.content.decode('utf-8', 'replace')

    if type(request_body)  == "str" and len(request_body)  > 1000: request_body  = "Request body too long"
    if type(response_body) == "str" and len(response_body) > 1000: response_body = "Response body too long"

    # get the hostname of linux machine that script running on. And also get it's IP address
    hostname = os.popen("hostname").read().strip()
    ip_address = os.popen("hostname -I").read().strip()

    log_entry = {
        "server": hostname,
        "server_ip": ip_address,
        "timestamp": datetime.now().isoformat(),
        "status_code": response.status_code,
        "reason": response.reason,
        "http_version": response.http_version,
        "method": request.method,
        "scheme": request.scheme,
        "host": request.host,
        "site": request.pretty_host,
        "path": request.path.split("?")[0],
        "query": request.query,
        "request_headers": request_headers,
        "response_headers": response_headers,
        "request_body": request_body,
        "response_body": response_body,
        # "url": request.url,
        # "response_length": len(response_body),
        # "response_time": response.timestamp_end - response.timestamp_start,
    }

    return {k: v for k,v in log_entry.items() if v}


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
    # direction = "->" if message.from_client else "<-"
    # message_content = message.content.decode('utf-8', 'ignore')  # Assuming it's text. Use 'ignore' to avoid decoding errors 

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "websocket",
        "id": flow.id,
        # "message_direction": direction,
        # "message_content": message_content,
        "messages": list(flow.websocket.messages)
        # Additional fields as necessary
    }

    return log_entry
