from datetime import datetime


def datetime_to_db(value: datetime | None) -> str | None:
    """
    Converts domain datetime to SQLite TEXT.

    All stored datetimes are normalized to UTC ISO-8601.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).isoformat()


from datetime import datetime, timezone


def dt_from_sqlite(
    value: str | int | datetime | None,
) -> datetime | None:
    """
    Converts SQLite datetime value to timezone-aware UTC datetime.

    Supported values:
    - None -> None
    - datetime
    - ISO-8601 string
    - Unix timestamp as int

    Invalid values raise an exception instead of silently
    becoming datetime.now().
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value

    elif isinstance(value, int):
        dt = datetime.fromtimestamp(
            value,
            tz=timezone.utc,
        )

    elif isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            try:
                timestamp = int(value)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid SQLite datetime value: {value!r}"
                ) from exc

            dt = datetime.fromtimestamp(
                timestamp,
                tz=timezone.utc,
            )

    else:
        raise TypeError(
            "SQLite datetime value must be "
            "str, int, datetime or None"
        )

    if dt.tzinfo is None:
        return dt.replace(
            tzinfo=timezone.utc,
        )

    return dt.astimezone(
        timezone.utc,
    )


def dt_to_sqlite_iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")



