import argparse

from client.network.tcp_client import WhiteboardClient

from shared.constants import DEFAULT_PORT


def main():

    parser = argparse.ArgumentParser(
        description="WhiteBoard Terminal Client"
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="IP address of the server."
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Server port."
    )

    parser.add_argument(
        "--username",
        required=True,
        help="Username for this client."
    )

    args = parser.parse_args()

    client = WhiteboardClient(
        host=args.host,
        port=args.port,
        username=args.username
    )

    try:
        client.connect()

        print("\nCommands:")
        print("  Type a message and press Enter to broadcast.")
        print("  /ping  - Check server connection.")
        print("  /quit  - Disconnect and exit.\n")

        while client.running.is_set():

            try:
                text = input("> ").strip()

            except (EOFError, KeyboardInterrupt):
                break

            if not text:
                continue

            if text == "/quit":
                break

            elif text == "/ping":
                client.ping()

            else:
                client.send_chat(text)

    except (ConnectionError, OSError, ValueError) as error:
        print(f"Client error: {error}")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()