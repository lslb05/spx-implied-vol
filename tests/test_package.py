import pytest

from vol_implicita_spx.config import Settings


def test_reads_settings_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOL_IMPLICITA_SPX_LOG_LEVEL", "DEBUG")

    assert Settings().log_level == "DEBUG"
