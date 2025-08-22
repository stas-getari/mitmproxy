import json

from utils import process_request_response

from mitmproxy import http


def response(flow: http.HTTPFlow) -> None:
    log_entry = process_request_response(flow)

    with open("flow_log.jsonl", "a") as log_file:
        json.dump(log_entry, log_file)
        log_file.write("\n")
