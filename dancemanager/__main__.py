import sys
import importlib
from dancemanager.cli import cli


def main():
    cli(standalone_mode=False)


if __name__ == "__main__":
    main()
