"""
Main entrance file
"""


from source.options import initialize
from source.application import App, parse_arguments


def main():
    initialize()
    args = parse_arguments()
    app = App(
        address=(args.address, args.port),
        ssl_keys=(args.certificate, args.private_key))
    app.run()


if __name__ == "__main__":
    main()
