"""
Main entrance file
"""


from source.application import App


def main():
    app = App(
        address=("0.0.0.0", 8080),
        ssl_keys=None)
    app.run()


if __name__ == "__main__":
    main()
