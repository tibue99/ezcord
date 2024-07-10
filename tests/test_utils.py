import ezcord


def test_big_numbers():
    assert ezcord.format_number(1_000) == "1k"
    assert ezcord.format_number(1_000_000) == "1M"
    assert ezcord.format_number(1_100_000) == "1.1M"
