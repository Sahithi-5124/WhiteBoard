import json
import socket
import struct
import time
import uuid

from shared.constants import (
    PROTOCOL_VERSION,
    MAX_MESSAGE_SIZE
)


def create_message(
    message_type,
    payload=None,
    room_id=None,
    sender_id=None
):
    """
    Creates a message using the common protocol envelope.
    """

    return {
        "protocol_version": PROTOCOL_VERSION,
        "type": message_type,
        "message_id": uuid.uuid4().hex,
        "room_id": room_id,
        "sender_id": sender_id,
        "timestamp": int(time.time()),
        "payload": payload if payload is not None else {}
    }


def send_message(sock, message, send_lock=None):
    """
    Serializes a message and sends it using length-prefix framing.

    Format:
        4-byte unsigned big-endian length
        JSON message bytes
    """

    try:
        json_data = json.dumps(
            message,
            ensure_ascii=False,
            separators=(",", ":")
        ).encode("utf-8")

        if len(json_data) == 0:
            raise ValueError("Empty messages are not allowed.")

        if len(json_data) > MAX_MESSAGE_SIZE:
            raise ValueError("Message exceeds maximum allowed size.")

        header = struct.pack("!I", len(json_data))
        packet = header + json_data

        if send_lock is not None:
            with send_lock:
                sock.sendall(packet)
        else:
            sock.sendall(packet)

    except (OSError, ValueError, TypeError) as error:
        raise error


def receive_exact(sock, size):
    """
    Reads exactly 'size' bytes from a TCP socket.

    TCP does not guarantee that one recv() call returns
    all the requested bytes.
    """

    data = bytearray()

    while len(data) < size:
        chunk = sock.recv(size - len(data))

        if not chunk:
            if len(data) == 0:
                return None

            raise ConnectionError(
                "Connection closed while receiving a message."
            )

        data.extend(chunk)

    return bytes(data)


def receive_message(sock):
    """
    Receives one complete length-prefixed JSON message.

    Returns:
        dict: The decoded message.
        None: If the peer disconnected before sending a new message.
    """

    header = receive_exact(sock, 4)

    if header is None:
        return None

    message_length = struct.unpack("!I", header)[0]

    if message_length == 0:
        raise ValueError("Received an empty message.")

    if message_length > MAX_MESSAGE_SIZE:
        raise ValueError("Received message exceeds maximum size.")

    json_data = receive_exact(sock, message_length)

    if json_data is None:
        raise ConnectionError(
            "Connection closed before the complete message arrived."
        )

    try:
        message = json.loads(json_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Received invalid JSON.") from error

    if not isinstance(message, dict):
        raise ValueError("A protocol message must be a JSON object.")

    return message