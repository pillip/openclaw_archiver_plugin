"""Allow running as `python -m openclaw_archiver`."""

from openclaw_archiver.server import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()
