import json
import socket
import struct

import pytest

from shared.protocol import (
    create_message,
    send_message,
    receive_message
)

from shared.constants import MAX_MESSAGE_SIZE


def test_message_creation():

    message = create_message(
        "CHAT_MESSAGE",
        payload={"text": "Hello"}
    )

    assert message["protocol_version"] == 1
    assert message["type"] == "CHAT_MESSAGE"
    assert message["payload"]["text"] == "Hello"
    assert "message_id" in message
    assert "timestamp" in message


def test_send_and_receive_message():

    sender, receiver = socket.socketpair()

    try:
        original = create_message(
            "CHAT_MESSAGE",
            payload={"text": "Hello WhiteBoard"}
        )

        send_message(sender, original)

        received = receive_message(receiver)

        assert received == original

    finally:
        sender.close()
        receiver.close()


def test_receive_fragmented_message():

    sender, receiver = socket.socketpair()

    try:
        message = create_message(
            "CHAT_MESSAGE",
            payload={"text": "Fragmented message"}
        )

        json_data = json.dumps(message).encode("utf-8")
        header = struct.pack("!I", len(json_data))

        packet = header + json_data

        # Deliberately send the packet in multiple pieces.
        sender.sendall(packet[:2])
        sender.sendall(packet[2:5])
        sender.sendall(packet[5:12])
        sender.sendall(packet[12:])

        received = receive_message(receiver)

        assert received == message

    finally:
        sender.close()
        receiver.close()


def test_reject_oversized_message():

    sender, receiver = socket.socketpair()

    try:
        oversized_length = MAX_MESSAGE_SIZE + 1

        header = struct.pack("!I", oversized_length)

        sender.sendall(header)

        with pytest.raises(ValueError):
            receive_message(receiver)

    finally:
        sender.close()
        receiver.close()


def test_reject_invalid_json():

    sender, receiver = socket.socketpair()

    try:
        invalid_data = b"{invalid json"

        header = struct.pack("!I", len(invalid_data))

        sender.sendall(header + invalid_data)

        with pytest.raises(ValueError):
            receive_message(receiver)

    finally:
        sender.close()
        receiver.close()


def test_clean_disconnect():

    sender, receiver = socket.socketpair()

    try:
        sender.close()

        received = receive_message(receiver)

        assert received is None

    finally:
        receiver.close()