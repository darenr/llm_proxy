import socket
import concurrent.futures
import json
import yaml
import logging
from rich.logging import RichHandler
from rich.traceback import install
import threading

# Install rich traceback handler
install()

# Configure logging with RichHandler
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

# Get the logger
logger = logging.getLogger("rich")

# Load configuration from YAML file
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Access API_ENDPOINTS from the config
API_ENDPOINTS = config["API_ENDPOINTS"]

# Configuration (rest of the config can also be in the YAML file)
PROXY_HOST = config.get("PROXY_HOST", "localhost")  # Use 'localhost' as default if not in YAML
PROXY_PORT = config.get("PROXY_PORT", 8080)  # Use 8080 as default if not in YAML


BUFFER_SIZE = 4096  # Adjust buffer size as needed


def handle_client(client_socket, addr):
    """
    Handles a client connection.

    This function receives the client socket and address,
    determines the target endpoint based on the request,
    and forwards the request/response between the client and target.
    """
    thread_name = threading.current_thread().name  # Get the thread name here
    logger.info(f"{thread_name} - Accepted connection from {addr}")
    try:
        # Receive initial data from the client
        data = client_socket.recv(BUFFER_SIZE)
        if not data:
            logger.warning(f"{thread_name} - Empty request received")
            client_socket.close()
            return

        logger.debug(f"{thread_name} - Received initial data: {data}")

        # Determine request type (streaming or regular)
        is_streaming = is_stream(data)

        # Determine target endpoint
        target_host, target_port = determine_target_endpoint(data, is_streaming)
        if not target_host:
            logger.warning(f"{thread_name} - No target endpoint found")
            client_socket.close()
            return

        logger.info(f"{thread_name} - Forwarding to {target_host}:{target_port}")

        # Forward the request to the target endpoint
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as target_socket:
            target_socket.connect((target_host, target_port))
            target_socket.sendall(data)  # Send initial data

            # Handle communication based on request type
            if is_streaming:
                handle_streaming(client_socket, target_socket)
            else:
                handle_regular_http(client_socket, target_socket)

    except Exception as e:
        logger.exception(f"{thread_name} - Error handling client request: {e}")
    finally:
        client_socket.close()
        logger.info(f"{thread_name} - Connection closed")


def is_stream(data):
    """
    Checks if the request indicates streaming (e.g., chunked encoding).

    This is a basic check and might need to be adjusted based on
    the specific streaming protocols used.
    """
    # Add more robust checks for different streaming scenarios
    return b"Transfer-Encoding: chunked" in data


def determine_target_endpoint(data, is_streaming):
    """
    Determines the target endpoint based on the request data.

    This function can be extended to handle various routing logic,
    including:
    - Header-based routing
    - Path-based routing
    - Payload-based routing (for non-streaming requests)
    - Default routing for unmatched requests
    """
    try:
        if not is_streaming:
            # For regular HTTP, try to extract payload for routing
            headers, payload_str = data.split(b"\r\n\r\n", 1)
            payload = json.loads(payload_str)
            logger.debug(f" - Parsed JSON payload: {payload}")
            # Extract original host and port from the 'Host' header
            host_header = next(
                (header for header in headers.split(b"\r\n") if header.startswith(b"Host: ")),
                b"",
            )
            original_host, original_port = parse_host_header(host_header)

            target_host, target_port = find_target_endpoint(payload)
            if not target_host:
                # Use original host and port as the default target
                return original_host, original_port
            return target_host, target_port
        else:
            # For streaming, you might use header or other info for routing
            # (Implement your streaming routing logic here)
            pass
    except:
        logger.exception(" - Error determining target endpoint")

    # If there's an error or no match, you might want to handle it differently
    # For now, returning None will cause the connection to be closed
    return None, None


def parse_host_header(host_header):
    """
    Parses the 'Host' header to extract the host and port.
    """
    try:
        host_header = host_header.decode().split(":")
        original_host = host_header[1].strip()  # Get the host
        original_port = (
            int(host_header[2].strip()) if len(host_header) > 2 else 80
        )  # Get the port (default to 80)
        return original_host, original_port
    except:
        logger.exception(" - Error parsing Host header")
        return None, None


def handle_streaming(client_socket, target_socket):
    """
    Handles bidirectional streaming between client and target.
    """
    thread_name = threading.current_thread().name
    logger.info(f"{thread_name} - Handling streaming connection")
    while True:
        try:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            target_socket.sendall(data)
            response = target_socket.recv(BUFFER_SIZE)
            if not response:
                break
            client_socket.sendall(response)
        except:
            logger.exception(f"{thread_name} - Error in streaming")
            break


def handle_regular_http(client_socket, target_socket):
    """
    Handles regular HTTP requests (non-streaming).
    """
    thread_name = threading.current_thread().name
    logger.info(f"{thread_name} - Handling regular HTTP connection")

    data = client_socket.recv(BUFFER_SIZE)
    while data:
        target_socket.sendall(data)
        data = client_socket.recv(BUFFER_SIZE)

    response = target_socket.recv(BUFFER_SIZE)
    while response:
        client_socket.sendall(response)
        response = target_socket.recv(BUFFER_SIZE)


def find_target_endpoint(payload):
    """
    Determines the target endpoint based on the JSON payload.

    This function implements the payload-based routing logic.
    You can customize the matching rules as needed.
    """
    for endpoint, config in API_ENDPOINTS.items():
        if payload.get(config["match_field"]) == config["match_value"]:
            return config["target_host"], config["target_port"]
    return None, None


def main():
    """Starts the reverse proxy server with a thread pool."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((PROXY_HOST, PROXY_PORT))
        server_socket.listen(10)
        logger.info(f"Reverse proxy listening on {PROXY_HOST}:{PROXY_PORT}")

        # Create a thread pool with a maximum of 10 worker threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            while True:
                client_socket, addr = server_socket.accept()
                executor.submit(handle_client, client_socket, addr)


if __name__ == "__main__":
    main()
