import pytest

from spx_implied_vol.config import Settings


def test_reads_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPX_IMPLIED_VOL_LOG_LEVEL", "DEBUG")

    assert Settings().log_level == "DEBUG"
