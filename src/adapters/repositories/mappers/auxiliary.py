from datetime import datetime, timezone


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


def dt_from_sqlite(value: str | int |datetime| None) -> datetime:
    """
    You said date_created INTEGER. But some parts of your code used ISO strings.
    This supports:
      - ISO string
      - unix timestamp int
      - None
    """
    dt = datetime.now()


    if isinstance(value, int):
        # interpret as unix timestamp seconds
        try:
            dt=datetime.fromtimestamp(value)
        except ValueError:
            dt=datetime.now()

    if isinstance(value, str):
        try:
            dt=datetime.fromisoformat(value)
        except ValueError:
            # try int-like string
            try:
                dt=datetime.fromtimestamp(int(value))
            except ValueError:
                dt=datetime.now()
    if isinstance(value,datetime):
        dt=value

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)



def dt_to_sqlite_iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")



