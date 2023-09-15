import ezcord


def test_libs():
    """Test compatibility with different Discord libraries."""
    assert ezcord.Bot(command_prefix="!")
