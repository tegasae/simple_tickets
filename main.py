import sys


def main() -> int:
    """
    Run all pytest tests.

    Examples:
        python main.py
        python main.py -v
        python main.py tests/domain
        python main.py tests/repositories -v
    """

    import pytest

    return pytest.main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())