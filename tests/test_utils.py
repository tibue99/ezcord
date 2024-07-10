import ezcord


def test_big_numbers():
    assert ezcord.format_number(1) == "1"
    assert ezcord.format_number(100) == "0.1K"
    assert ezcord.format_number(1_000) == "1K"
    assert ezcord.format_number(1_000_000) == "1M"
    assert ezcord.format_number(1_100_000) == "1.1M"
    assert ezcord.format_number(1_000_000_000) == "1B"

    # negative
    assert ezcord.format_number(-1) == "-1"
    assert ezcord.format_number(-100) == "-0.1K"
    assert ezcord.format_number(-1_000) == "-1K"
    assert ezcord.format_number(-1_000_000) == "-1M"
    assert ezcord.format_number(-1_100_000) == "-1.1M"
    assert ezcord.format_number(-1_000_000_000) == "-1B"

    # decimals and trailing zeros
    assert ezcord.format_number(1_550, decimal_places=2) == "1.55K"
    assert ezcord.format_number(1_550, decimal_places=3) == "1.55K"
    assert ezcord.format_number(1_550, decimal_places=3, trailing_zero=True) == "1.550K"
    assert ezcord.format_number(1_000, trailing_zero=True) == "1.0K"
    assert ezcord.format_number(1_000, decimal_places=2, trailing_zero=True) == "1.00K"
