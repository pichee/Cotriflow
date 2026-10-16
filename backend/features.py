from __future__ import annotations

import csv
import math
from datetime import datetime, timedelta
from pathlib import Path

from app.database import Base, SessionLocal, engine
from app.features import (
    CARACTERISTICAS,
    ESTACOES,
    MAPA_ESTACOES,
    RACOES,
    aplicar_features_dataframe,
    calcular_predicao_cliente,
    carregar_modelo,
    construir_features_registros,
    executar_pipeline_csv,
    normalizar_racao,
    parse_data,
    prever_dias,
    prever_vetor,
)
from app.models import Predicao


class _NumpyRandomState42:
    """Reproduz exatamente np.random.RandomState(42) para o train_test_split(test_size=0.30, random_state=42)."""

    def __init__(self, seed: int = 42) -> None:
        self.mt = [0] * 624
        self.mt[0] = seed & 0xFFFFFFFF
        for i in range(1, 624):
            self.mt[i] = (1812433253 * (self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) + i) & 0xFFFFFFFF
        self.pos = 624

    def uint32(self) -> int:
        if self.pos >= 624:
            for i in range(624):
                y = (self.mt[i] & 0x80000000) + (self.mt[(i + 1) % 624] & 0x7FFFFFFF)
                self.mt[i] = self.mt[(i + 397) % 624] ^ (y >> 1)
                if y & 1:
                    self.mt[i] ^= 0x9908B0DF
            self.pos = 0
        y = self.mt[self.pos]
        self.pos += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= y >> 18
        return y & 0xFFFFFFFF

    def rk_interval(self, mx: int) -> int:
        if mx == 0:
            return 0
        mask = mx
        mask |= mask >> 1
        mask |= mask >> 2
        mask |= mask >> 4
        mask |= mask >> 8
        mask |= mask >> 16
        while True:
            val = self.uint32() & mask
            if val <= mx:
                return val

    def permutation(self, n: int) -> list[int]:
        arr = list(range(n))
        for i in range(n - 1, 0, -1):
            j = self.rk_interval(i)
            arr[i], arr[j] = arr[j], arr[i]
        return arr


def rodar_script_predicao(atualizar_banco: bool = True) -> dict:
    base_dir = Path(__file__).resolve().parent
    csv_path = base_dir / "dados_predicoes.csv"
    registros = executar_pipeline_csv(csv_path)

    dados = [r for r in registros if r["dias_ate_proxima"] is not None]
    producao = [r for r in registros if r["dias_ate_proxima"] is None]

    # Divisão Treino / Teste 70/30 (train_test_split com random_state=42)
    n = len(dados)
    n_test = math.ceil(0.30 * n)
    perm = _NumpyRandomState42(42).permutation(n)
    teste_idx = perm[:n_test]
    treino_idx = perm[n_test:]
    treino = [dados[i] for i in treino_idx]
    teste = [dados[i] for i in teste_idx]

    mod = carregar_modelo()
    erros_modelo = [
        abs(r["dias_ate_proxima"] - prever_vetor(r, mod))
        for r in teste
    ]
    mae_modelo = round(sum(erros_modelo) / len(erros_modelo), 2)

    # Exportar previsoes_teste_30.csv (Etapa 7 da Versão A)
    teste_csv_path = base_dir / "previsoes_teste_30.csv"
    with open(teste_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Cliente", "Animal", "Qtd (Kg)", "Data Compra",
            "Prev. Dias", "Data Prevista", "Data Real", "Erro (Dias)",
        ])
        for r in teste:
            erro_int = int(abs(r["dias_previstos"] - int(r["dias_ate_proxima"])))
            writer.writerow([
                r["id_cliente"],
                r["animal"],
                int(r["quantidade_kg"]) if r["quantidade_kg"].is_integer() else r["quantidade_kg"],
                r["data"].strftime("%Y-%m-%d"),
                r["dias_previstos"],
                r["data_prevista"].strftime("%Y-%m-%d"),
                r["proxima_data"].strftime("%Y-%m-%d"),
                f"{erro_int} dias",
            ])

    if atualizar_banco:
        Base.metadata.create_all(bind=engine)
        registros_ordenados_data = sorted(
            registros,
            key=lambda r: (r["data"], r["id_cliente"]),
        )
        db = SessionLocal()
        try:
            db.query(Predicao).delete()
            novos_objetos = []
            linhas_sql = [
                "-- Dataset completo de Predições CotriFlow",
                f"-- Total de registros: {len(registros_ordenados_data)}",
                "",
            ]
            for r in registros_ordenados_data:
                obs = f"Previsão calculada com base no consumo de {r['animal']}."
                novos_objetos.append(
                    Predicao(
                        cliente=r["id_cliente"],
                        animal=r["animal"],
                        quantidade_kg=float(r["quantidade_kg"]),
                        data_compra=r["data"],
                        dias_previstos=int(r["dias_previstos"]),
                        data_previsao=r["data_prevista"],
                        data_real=r["proxima_data"],
                        observacao=obs,
                    )
                )
                dc_str = r["data"].strftime("%Y-%m-%d 00:00:00")
                dp_str = r["data_prevista"].strftime("%Y-%m-%d 00:00:00")
                dr_sql = (
                    f"'{r['proxima_data'].strftime('%Y-%m-%d 00:00:00')}'"
                    if r["proxima_data"] is not None
                    else "NULL"
                )
                linhas_sql.append(
                    "INSERT INTO predicoes (cliente, animal, quantidade_kg, data_compra, "
                    "dias_previstos, data_previsao, data_real, observacao) VALUES "
                    f"('{r['id_cliente']}', '{r['animal']}', {float(r['quantidade_kg']):.1f}, "
                    f"'{dc_str}', {int(r['dias_previstos'])}, '{dp_str}', {dr_sql}, '{obs}');"
                )
            db.add_all(novos_objetos)
            db.commit()

            sql_path = base_dir / "predicoes_dataset.sql"
            with open(sql_path, "w", encoding="utf-8") as f_sql:
                f_sql.write("\n".join(linhas_sql) + "\n")
        finally:
            db.close()

    agenda = sorted(producao, key=lambda r: (r["data_prevista"], r["id_cliente"]))
    return {
        "total_registros": len(registros),
        "total_dados_historico": len(dados),
        "total_producao": len(producao),
        "modelo_vencedor": mod["model_name"],
        "mae_teste": mae_modelo,
        "agenda_producao": agenda,
    }


if __name__ == "__main__":
    res = rodar_script_predicao(atualizar_banco=True)
    print(f"Modelo vencedor: {res['modelo_vencedor']} (MAE Teste 30%: {res['mae_teste']} dias)")
    print(f"Total de registros atualizados no banco: {res['total_registros']}")
    print("\nAgenda de Produção (ordenada por urgência - primeiros 15):")
    for item in res["agenda_producao"][:15]:
        print(
            f"  {item['id_cliente']} | {item['animal']:<8} | {item['quantidade_kg']:>6.0f} kg | "
            f"Compra: {item['data'].strftime('%Y-%m-%d')} | "
            f"Prev: {item['dias_previstos']:>2} dias -> {item['data_prevista'].strftime('%Y-%m-%d')}"
        )
