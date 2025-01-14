import unittest
import socket
import threading
import json
from proxy import handle_client, is_stream, determine_target_endpoint, find_target_endpoint  # Import functions from your proxy script

# Mock socket for testing
class MockSocket:
    def __init__(self):
        self.received_data = b''
        self.sent_data = b''

    def recv(self, bufsize):
        return self.received_data

    def sendall(self, data):
        self.sent_data += data

    def close(self):
        pass

class ProxyTests(unittest.TestCase):

    def test_is_stream_chunked(self):
        data = b'Transfer-Encoding: chunked\r\n'
        self.assertTrue(is_stream(data))

    def test_is_stream_not_chunked(self):
        data = b'Content-Type: application/json\r\n'
        self.assertFalse(is_stream(data))

    def test_determine_target_endpoint_json(self):
        data = b'POST /api/endpoint HTTP/1.1\r\nContent-Type: application/json\r\n\r\n{"field1": "value1"}'
        target_host, target_port = determine_target_endpoint(data, False)
        self.assertEqual(target_host, "api1.example.com")
        self.assertEqual(target_port, 80)

    def test_determine_target_endpoint_no_match(self):
        data = b'POST /api/endpoint HTTP/1.1\r\nContent-Type: application/json\r\n\r\n{"field1": "value2"}'
        target_host, target_port = determine_target_endpoint(data, False)
        self.assertEqual(target_host, "default_api.example.com")  # Assuming default target
        self.assertEqual(target_port, 80)

    def test_determine_target_endpoint_streaming(self):
        data = b'POST /api/stream HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n'
        # Implement your streaming routing logic and assertions here
        # For example:
        # target_host, target_port = determine_target_endpoint(data, True)
        # self.assertEqual(target_host, "streaming_api.example.com")
        pass  # Replace with your streaming test

    def test_find_target_endpoint(self):
        payload = {"field2": "value2"}
        target_host, target_port = find_target_endpoint(payload)
        self.assertEqual(target_host, "api2.example.com")
        self.assertEqual(target_port, 8080)

    def test_handle_client_regular_http(self):
        client_socket = MockSocket()
        client_socket.received_data = b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n'
        addr = ("127.0.0.1", 50000)
        
        # Start handle_client in a separate thread
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()
        thread.join()  # Wait for the thread to finish

        # Add assertions to check client_socket.sent_data
        # This will depend on your default target and its response
        # For example:
        # self.assertIn(b'HTTP/1.1 200 OK', client_socket.sent_data)

    def test_handle_client_streaming(self):
        client_socket = MockSocket()
        client_socket.received_data = b'POST /stream HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n'
        addr = ("127.0.0.1", 50001)
        
        # Start handle_client in a separate thread
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()
        thread.join()  # Wait for the thread to finish

        # Add assertions to check client_socket.sent_data for streaming
        # This will depend on your streaming target and its response
        pass  # Replace with your streaming test

if __name__ == '__main__':
    unittest.main()
