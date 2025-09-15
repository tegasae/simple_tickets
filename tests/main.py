# content of myinvoke.py
import pytest

pytest.main(["--cov","--cov-report=term-missing","-s" ])
