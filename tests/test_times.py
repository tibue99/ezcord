from datetime import datetime, timedelta

import ezcord


def test_convert_time():
    dt = ezcord.set_utc(datetime.utcnow())

    assert isinstance(ezcord.convert_dt(dt), str)
    assert isinstance(ezcord.convert_dt(timedelta(seconds=5)), str)
    assert isinstance(ezcord.convert_time(5), str)


def test_dc_timestamp():
    result = ezcord.dc_timestamp(0)
    assert result.startswith("<t:") and result.endswith(":R>")


def test_convert_so_seconds():
    assert ezcord.convert_to_seconds("1m 9s") == 69
    assert ezcord.convert_to_seconds("1.5m") == 90
    assert ezcord.convert_to_seconds("1,5 min") == 90
    assert ezcord.convert_to_seconds("1h 5m 10s") == 3910
