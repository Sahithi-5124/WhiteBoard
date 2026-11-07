import socket
import threading

from shared.protocol import (
    create_message,
    send_message,
    receive_message
)

from shared.constants import (
    CONNECT,
    CONNECT_SUCCESS,
    CONNECT_ERROR,
    DISCONNECT,
    PING,
    CHAT_MESSAGE
)


class WhiteboardClient:

    def __init__(self, host, port, username):

        self.host = host
        self.port = port
        self.username = username

        self.sock = None

        self.user_id = None

        self.send_lock = threading.Lock()

        self.running = threading.Event()
        self.receive_thread = None

    def connect(self):
        """
        Connects to the server and performs the handshake.
        """

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.sock.connect((self.host, self.port))

        connect_message = create_message(
            CONNECT,
            payload={"username": self.username}
        )

        send_message(self.sock, connect_message)

        response = receive_message(self.sock)

        if response is None:
            raise ConnectionError(
                "Server closed the connection during handshake."
            )

        if response.get("type") != CONNECT_SUCCESS:

            error = response.get("payload", {}).get(
                "message",
                "Connection rejected."
            )

            raise ConnectionError(error)

        self.user_id = response["payload"]["user_id"]

        print(
            f"Connected as {self.username}. "
            f"Your ID is {self.user_id}"
        )

        self.running.set()

        self.receive_thread = threading.Thread(
            target=self.receive_loop,
            daemon=True
        )

        self.receive_thread.start()

    def send(self, message):
        """
        Sends a protocol message to the server.
        """

        if not self.running.is_set():
            raise ConnectionError("Client is not connected.")

        send_message(
            self.sock,
            message,
            self.send_lock
        )

    def send_chat(self, text):

        message = create_message(
            CHAT_MESSAGE,
            payload={"text": text}
        )

        self.send(message)

    def ping(self):

        message = create_message(PING)

        self.send(message)

    def receive_loop(self):
        """
        Continuously receives messages from the server.
        """

        try:
            while self.running.is_set():

                message = receive_message(self.sock)

                if message is None:
                    break

                message_type = message.get("type")
                payload = message.get("payload", {})

                if message_type == "CHAT_BROADCAST":

                    username = payload.get(
                        "username",
                        "Unknown"
                    )

                    text = payload.get("text", "")

                    print(f"\n[{username}]: {text}")

                elif message_type == "USER_JOINED":

                    print(
                        f"\n{payload.get('username')} joined."
                    )

                elif message_type == "USER_LEFT":

                    print(
                        f"\n{payload.get('username')} left."
                    )

                elif message_type == "PONG":

                    print("\nServer is responding.")

                elif message_type == "ERROR":

                    print(
                        "\nServer error:",
                        payload.get("message")
                    )

                else:
                    print(
                        "\nReceived:",
                        message_type,
                        payload
                    )

        except (ConnectionError, OSError, ValueError) as error:
            if self.running.is_set():
                print(f"\nConnection lost: {error}")

        finally:
            self.running.clear()

            if self.sock:
                try:
                    self.sock.close()
                except OSError:
                    pass

            print("\nDisconnected from server.")

    def disconnect(self):
        """
        Requests a normal disconnection.
        """

        if not self.running.is_set():
            return

        try:
            message = create_message(DISCONNECT)
            send_message(
                self.sock,
                message,
                self.send_lock
            )
        except (OSError, ValueError):
            pass

        self.running.clear()

        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            self.sock.close()
        except OSError:
            pass

        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2)