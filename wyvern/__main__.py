import argparse

from wyvern.server import server


def main() -> None:
    parser = argparse.ArgumentParser(description="Wyvern — Draconic LSP server")
    parser.add_argument("--tcp", action="store_true", help="Use TCP transport instead of stdio")
    parser.add_argument("--stdio", action="store_true", help="Use stdio transport (default)")
    parser.add_argument("--host", default="127.0.0.1", help="TCP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2087, help="TCP port (default: 2087)")
    args = parser.parse_args()

    if args.tcp:
        server.start_tcp(args.host, args.port)
    else:
        server.start_io()


if __name__ == "__main__":
    main()
