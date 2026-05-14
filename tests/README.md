# Supplemental pytest tests for `simple_tickets`

These tests extend the previous test suite and focus on other domain entities and services:

- value objects;
- Account / NoAccount;
- Client;
- Admin / User entities;
- RBAC Authorizer / RoleManager / RoleStore;
- ticket policies;
- ticket shared components;
- EmployeeActorHelper / EmployeeHelper;
- ClientApplicationService;
- UserApplicationService.

The web layer is intentionally skipped.

## Run

Copy the `tests/` directory and `pytest.ini` into the project root, then run:

```bash
pip install pytest
pytest
```

Current result against the uploaded project snapshot:

```text
59 passed, 2 xfailed
```

The two `xfail` tests document an existing issue: `AdminRole` and `UserRole` have `__post_init__` validation methods, but they are not decorated as dataclasses, so the validation is not currently executed.
