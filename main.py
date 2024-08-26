"""
The mighty silly webserver written in python for no good reason
"""


import ssl
import time
import socket
import signal
import threading
from src import APIv1
from src.config import *
from src.request import *
from src.status_code import *
from src.file_man import PATH_MAP


# typing
usocket = socket.socket | ssl.SSLSocket


class HTTPServer:
    """
    The mightier HTTP server!
    Now uses threading
    """

    def __init__(
            self,
            *,
            port: int,
            enable_ssl: bool = True,
            path_map: dict[str, dict] | None = None
    ):
        # Sockets
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if enable_ssl:
            # SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.check_hostname = False
            context.load_cert_chain(
                certfile=r"C:\Certbot\live\qubane.ddns.net\fullchain.pem",  # use your own path here
                keyfile=r"C:\Certbot\live\qubane.ddns.net\privkey.pem")  # here too
            self.sock: usocket = context.wrap_socket(sock, server_side=True)
        else:
            self.sock: usocket = sock
        self.port: int = port

        # client thread list
        self.client_threads: list[threading.Thread] = []
        self.semaphore: threading.Semaphore = threading.Semaphore(CLIENT_MAX_PROCESS)

        # add signaling
        self.stop_event = threading.Event()
        signal.signal(signal.SIGINT, self._signal_interrupt)

        # path mapping
        self.path_map: dict[str, dict] = path_map if path_map else PATH_MAP

    def _signal_interrupt(self, *args):
        """
        Checks for CTRL+C keyboard interrupt, to properly stop the HTTP server
        """

        # stop all threads
        self.stop_event.set()
        for thread in self.client_threads:
            thread.join()

    def start(self):
        """
        Method to start the web server
        """

        # bind and start listening to port
        self.sock.bind(('', self.port))
        self.sock.setblocking(False)
        self.sock.listen()

        # listen and respond handler
        while not self.stop_event.is_set():
            # accept new client
            client = self._accept()
            if client is None:
                continue

            # create thread for new client and append it to the list
            th = threading.Thread(target=self._client_thread, args=[client])
            self.client_threads.append(th)
            th.start()

        # close server socket
        self.sock.close()

    def _client_thread(self, client: usocket):
        """
        Handles getting client's requests
        :param client: client ssl socket
        """

        self.semaphore.acquire()
        try:
            request = self._recv_request(client)
            if request is not None:
                self._client_request_handler(client, request)
        except ssl.SSLEOFError:
            pass
        except OSError as e:
            print(f"Request dropped due to: {e}")
        except Exception as e:
            print(e)

        # Remove self from thread list and close the connection
        self.client_threads.remove(threading.current_thread())
        self.semaphore.release()
        client.close()

    def _client_request_handler(self, client: usocket, request: Request):
        """
        Handles responses to client's requests
        :param client: client
        :param request: client's request
        """

        match request.type:
            case "GET":
                response = self._handle_get(client, request)
            case _:
                response = Response(b'', STATUS_CODE_NOT_FOUND)

        # process header data
        if response.headers.get("Connection") is None:
            response.headers["Connection"] = "close"

        # generate basic message
        message = b'HTTP/1.1 ' + response.status.__bytes__() + b'\r\n'
        for key, value in response.headers.items():
            message += f"{key}: {value}\r\n".encode("utf8")
        message += b'\r\n'

        # send message
        client.sendall(message)
        for packet in response.get_data_stream():
            client.sendall(packet)

            # check for stop event
            if self.stop_event.is_set():
                break

    def _handle_get(self, client: usocket, request: Request) -> Response:
        """
        Handles GET requests from a client
        """

        split_path = request.path.split("/", maxsplit=16)[1:]
        if request.path in self.path_map:  # assume browser
            filepath = self.path_map[request.path]["path"]
            filedata = self.fetch_file(filepath)
            response = Response(b'', STATUS_CODE_OK, data_stream=filedata)

            return response
        elif len(split_path) >= 2 and split_path[0] in API_VERSIONS:  # assume script
            # unsupported API version
            if not API_VERSIONS[split_path[0]]:
                if request.type == "GET":
                    return Response(b'API unavailable / deprecated', STATUS_CODE_BAD_REQUEST)

            # return API response
            return APIv1.api_call(client, request)
        else:
            return Response(b'', STATUS_CODE_NOT_FOUND)

    def _handle_post(self, client: usocket, request: Request) -> Response:
        """
        Handles POST request from a client
        """

    def _recv_request(self, client: usocket) -> Request | None:
        """
        Receive request from client
        :return: request
        :raises: anything that recv raises
        """

        buffer = bytearray()
        while not self.stop_event.is_set():
            if len(msg := client.recv(BUFFER_LENGTH)) == 0:
                break
            buffer += msg
            if buffer[-4:] == b'\r\n\r\n':
                return Request.create(buffer)
            if len(buffer) > BUFFER_MAX_SIZE:  # ignore big messages
                break
        return None

    def _accept(self) -> usocket | None:
        """
        socket.accept, but for more graceful closing
        """

        while not self.stop_event.is_set():
            try:
                if len(self.client_threads) < CLIENT_MAX_AMOUNT:
                    return self.sock.accept()[0]
            except BlockingIOError:
                time.sleep(0.005)
            except ssl.SSLEOFError:
                break
            except OSError as e:
                print(f"Client dropped due to: {e}")
                break
        return None

    def fetch_file(self, path: str) -> tuple[Generator[bytes, None, None], dict[str, str]] | None:
        """
        Fetches file
        :param path: filepath
        :return: data stream, headers
        """

        if path in self.path_map:
            filepath = self.path_map[path]["path"]
            headers = self.path_map[path]["headers"]
            with open(filepath, "rb") as file:
                yield file.read(BUFFER_LENGTH), headers


def main():

    server = HTTPServer(port=13700, enable_ssl=False)
    server.start()


if __name__ == '__main__':
    main()
