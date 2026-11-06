import argparse

from server.network.tcp_server import WhiteboardServer

from shared.constants import DEFAULT_HOST, DEFAULT_PORT


def main():

    parser = argparse.ArgumentParser(
        description="WhiteBoard TCP Server"
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="IP address to bind the server to."
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port number for the server."
    )

    args = parser.parse_args()

    server = WhiteboardServer(
        host=args.host,
        port=args.port
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nStopping server...")

    finally:
        server.shutdown()


if __name__ == "__main__":
    main()