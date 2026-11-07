import socket
import threading
import time

import pytest

from server.network.tcp_server import WhiteboardServer

from shared.protocol import (
    create_message,
    send_message,
    receive_message
)

from shared.constants import (
    CONNECT,
    CONNECT_SUCCESS,
    CHAT_MESSAGE,
    CHAT_BROADCAST,
    DISCONNECT,
    USER_LEFT
)


def connect_test_client(port, username):

    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client_socket.connect(("127.0.0.1", port))

    message = create_message(
        CONNECT,
        payload={"username": username}
    )

    send_message(client_socket, message)

    response = receive_message(client_socket)

    assert response["type"] == CONNECT_SUCCESS

    return client_socket


def receive_until_type(sock, expected_type, max_messages=10):

    for _ in range(max_messages):

        message = receive_message(sock)

        if message is None:
            break

        if message.get("type") == expected_type:
            return message

    raise AssertionError(
        f"Did not receive message type {expected_type}"
    )


@pytest.fixture
def running_server():

    server = WhiteboardServer(
        host="127.0.0.1",
        port=0
    )

    server_thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )

    server_thread.start()

    ready = server.ready.wait(timeout=5)

    if not ready:
        server.shutdown()
        raise RuntimeError("Test server failed to start.")

    yield server

    server.shutdown()
    server_thread.join(timeout=3)


def test_two_clients_can_broadcast_and_disconnect(running_server):

    port = running_server.bound_port

    client1 = None
    client2 = None

    try:
        # Connect the first client.
        client1 = connect_test_client(port, "Alice")

        # Connect the second client.
        client2 = connect_test_client(port, "Bob")

        # Alice sends a message.
        chat = create_message(
            CHAT_MESSAGE,
            payload={"text": "Hello Bob"}
        )

        send_message(client1, chat)

        # Bob should receive the broadcast.
        received = receive_until_type(
            client2,
            CHAT_BROADCAST
        )

        assert received["payload"]["text"] == "Hello Bob"
        assert received["payload"]["username"] == "Alice"

        # Bob disconnects.
        send_message(
            client2,
            create_message(DISCONNECT)
        )

        client2.close()
        client2 = None

        # Alice should receive a USER_LEFT event.
        left_event = receive_until_type(
            client1,
            USER_LEFT
        )

        assert left_event["payload"]["username"] == "Bob"

    finally:

        if client1:
            client1.close()

        if client2:
            client2.close()