from datetime import date

import psycopg
import pytest

from vol_implicita_spx.taxa_livre_risco import TaxaIndisponivel, taxa_3_meses


def test_devolve_a_taxa_mais_recente_conhecida_na_data(
    conexao: psycopg.Connection,
) -> None:
    conexao.execute(
        """
        INSERT INTO series_vintage
            (fonte, serie, data_evento, data_publicacao, vigente_ate, valor,
             data_disponibilidade)
        VALUES ('fred', 'DGS3MO', '2026-06-01', '2026-06-02', '2026-06-08',
                5.33, '2026-06-02')
        """
    )

    taxa = taxa_3_meses(conexao, em=date(2026, 6, 5))

    assert taxa == pytest.approx(0.0533)


def test_serie_ausente_levanta_erro_com_instrucao(
    conexao: psycopg.Connection,
) -> None:
    with pytest.raises(TaxaIndisponivel, match="DGS3MO"):
        taxa_3_meses(conexao, em=date(2026, 6, 5))
