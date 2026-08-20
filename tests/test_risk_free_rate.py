from datetime import date

import psycopg
import pytest

from spx_implied_vol.risk_free_rate import RateUnavailable, rate_3_months


def test_returns_the_most_recent_rate_known_at_the_date(
    connection: psycopg.Connection,
) -> None:
    connection.execute(
        """
        INSERT INTO series_vintage
            (fonte, serie, data_evento, data_publicacao, vigente_ate, valor,
             data_disponibilidade)
        VALUES ('fred', 'DGS3MO', '2026-06-01', '2026-06-02', '2026-06-08',
                5.33, '2026-06-02')
        """
    )

    rate = rate_3_months(connection, at=date(2026, 6, 5))

    assert rate == pytest.approx(0.0533)


def test_missing_series_raises_with_instructions(
    connection: psycopg.Connection,
) -> None:
    with pytest.raises(RateUnavailable, match="DGS3MO"):
        rate_3_months(connection, at=date(2026, 6, 5))
