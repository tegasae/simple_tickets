import pytest
#pytest -v -rxX
pytest.main(["--cov","--cov-report=term-missing","-s" ])
# main.py
exit()
import sys
import pytest


def main() -> int:
    """
    Run all pytest tests.

    Examples:
        python main.py
        python main.py -v
        python main.py tests/domain
        python main.py tests/repositories -v
    """

    args = sys.argv[1:]

    if not args:
        args = ["tests", "-v"]

    return pytest.main(args)


if __name__ == "__main__":
    raise SystemExit(main())