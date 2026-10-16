from __future__ import annotations

import csv
import json
import math
import os
import statistics
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

RACOES = ["Aves", "Bovinos", "Equinos", "Ovinos", "Peixes", "Suinos"]
ESTACOES = ["Inverno", "Outono", "Primavera", "Verao"]

MAPA_ESTACOES = {
    12: "Verao", 1: "Verao", 2: "Verao",
    3: "Outono", 4: "Outono", 5: "Outono",
    6: "Inverno", 7: "Inverno", 8: "Inverno",
    9: "Primavera", 10: "Primavera", 11: "Primavera",
}

CARACTERISTICAS = (
    ["quantidade_kg", "mes"]
    + [f"racao_{r}" for r in RACOES]
    + [
        "dias_desde_ultima",
        "media_acumulada",
        "desvio_padrao_acumulado",
        "qtd_acumulada",
    ]
    + [f"estacao_{e}" for e in ESTACOES]
)

_MODEL_PATH = Path(__file__).resolve().parent / "modelo_treinado.json"
_CSV_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "dados_predicoes.csv"
_CACHED_MODEL: dict[str, Any] | None = None


def normalizar_racao(tipo_racao: str | None) -> str:
    if not tipo_racao:
        return ""
    limpo = unicodedata.normalize("NFKD", str(tipo_racao).strip())
    limpo = "".join(c for c in limpo if not unicodedata.combining(c)).lower()
    mapa = {
        "ave": "Aves",
        "aves": "Aves",
        "frango": "Aves",
        "frangos": "Aves",
        "bovino": "Bovinos",
        "bovinos": "Bovinos",
        "gado": "Bovinos",
        "equino": "Equinos",
        "equinos": "Equinos",
        "cavalo": "Equinos",
        "cavalos": "Equinos",
        "ovino": "Ovinos",
        "ovinos": "Ovinos",
        "ovelha": "Ovinos",
        "ovelhas": "Ovinos",
        "peixe": "Peixes",
        "peixes": "Peixes",
        "suino": "Suinos",
        "suinos": "Suinos",
        "porco": "Suinos",
        "porcos": "Suinos",
    }
    return mapa.get(limpo, str(tipo_racao).strip())


def parse_data(valor: datetime | str) -> datetime:
    if isinstance(valor, datetime):
        return datetime(valor.year, valor.month, valor.day)
    texto = str(valor).strip().replace("T", " ").split(" ")[0]
    return datetime.strptime(texto[:10], "%Y-%m-%d")


def aplicar_features_dataframe(df: Any) -> tuple[Any, list[str]]:
    """Versão B (features.py): criação explícita das colunas em um DataFrame pandas."""
    df["mes"] = df["data"].dt.month
    for r in RACOES:
        df[f"racao_{r}"] = (df["tipo_racao"] == r).astype(int)
    caracteristicas = ["quantidade_kg", "mes"] + [f"racao_{r}" for r in RACOES] + ["dias_desde_ultima"]

    df["media_acumulada"] = (
        df.groupby("id_cliente")["dias_desde_ultima"].expanding().mean().reset_index(level=0, drop=True)
    )
    caracteristicas += ["media_acumulada"]

    df["desvio_padrao_acumulado"] = (
        df.groupby("id_cliente")["dias_desde_ultima"].expanding().std().fillna(0).reset_index(level=0, drop=True)
    )
    caracteristicas += ["desvio_padrao_acumulado"]

    df["qtd_acumulada"] = (
        df.groupby("id_cliente")["quantidade_kg"].expanding().mean().reset_index(level=0, drop=True)
    )
    caracteristicas += ["qtd_acumulada"]

    df["estacao"] = df["mes"].map(MAPA_ESTACOES)
    for e in ESTACOES:
        df[f"estacao_{e}"] = (df["estacao"] == e).astype(int)
        caracteristicas.append(f"estacao_{e}")

    return df, caracteristicas


def construir_features_registros(
    registros: list[dict[str, Any]],
    mediana_padrao: float | None = None,
) -> tuple[list[dict[str, Any]], float]:
    """Executa a engenharia de recursos completa (Versão A + Versão B) sobre registros."""
    if not registros:
        return [], (mediana_padrao if mediana_padrao is not None else 29.0)

    preparados: list[dict[str, Any]] = []
    for idx, reg in enumerate(registros):
        cliente = str(reg.get("id_cliente") or reg.get("cliente") or "").strip()
        data_dt = parse_data(reg.get("data") or reg.get("data_compra"))
        tipo_orig = reg.get("tipo_racao") if reg.get("tipo_racao") is not None else reg.get("animal")
        tipo_norm = normalizar_racao(tipo_orig)
        qtd = float(reg.get("quantidade_kg") if reg.get("quantidade_kg") is not None else 0.0)
        preparados.append({
            **reg,
            "_orig_idx": idx,
            "id_cliente": cliente,
            "cliente": cliente,
            "data": data_dt,
            "animal": str(tipo_orig).strip() if tipo_orig else tipo_norm,
            "tipo_racao": tipo_norm,
            "quantidade_kg": qtd,
        })

    preparados.sort(key=lambda x: (x["id_cliente"], x["data"], x["_orig_idx"]))

    por_cliente: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in preparados:
        por_cliente[item["id_cliente"]].append(item)

    intervalos_validos: list[float] = []
    for _, lista in por_cliente.items():
        for i, item in enumerate(lista):
            if i + 1 < len(lista):
                item["proxima_data"] = lista[i + 1]["data"]
                item["dias_ate_proxima"] = float((lista[i + 1]["data"] - item["data"]).days)
            else:
                item["proxima_data"] = None
                item["dias_ate_proxima"] = None

            if i > 0:
                diff_dias = float((item["data"] - lista[i - 1]["data"]).days)
                item["dias_desde_ultima"] = diff_dias
                intervalos_validos.append(diff_dias)
            else:
                item["dias_desde_ultima"] = None

    if mediana_padrao is not None:
        mediana = float(mediana_padrao)
    elif intervalos_validos:
        mediana = float(statistics.median(intervalos_validos))
    else:
        mediana = 29.0

    for item in preparados:
        if item["dias_desde_ultima"] is None:
            item["dias_desde_ultima"] = mediana

    for _, lista in por_cliente.items():
        hist_ddu: list[float] = []
        hist_qtd: list[float] = []
        for item in lista:
            hist_ddu.append(float(item["dias_desde_ultima"]))
            hist_qtd.append(float(item["quantidade_kg"]))

            mes = item["data"].month
            item["mes"] = float(mes)
            for r in RACOES:
                item[f"racao_{r}"] = 1.0 if item["tipo_racao"] == r else 0.0

            item["media_acumulada"] = sum(hist_ddu) / len(hist_ddu)
            item["desvio_padrao_acumulado"] = (
                statistics.stdev(hist_ddu) if len(hist_ddu) > 1 else 0.0
            )
            item["qtd_acumulada"] = sum(hist_qtd) / len(hist_qtd)

            estacao = MAPA_ESTACOES[mes]
            item["estacao"] = estacao
            for e in ESTACOES:
                item[f"estacao_{e}"] = 1.0 if estacao == e else 0.0

    return preparados, mediana


def carregar_modelo() -> dict[str, Any]:
    global _CACHED_MODEL
    if _CACHED_MODEL is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(f"Modelo treinado não encontrado em {_MODEL_PATH}")
        with open(_MODEL_PATH, "r", encoding="utf-8") as f:
            _CACHED_MODEL = json.load(f)
    return _CACHED_MODEL


def prever_vetor(vetor_ou_dict: list[float] | dict[str, Any], modelo: dict[str, Any] | None = None) -> float:
    mod = modelo or carregar_modelo()
    carac = mod["caracteristicas"]
    if isinstance(vetor_ou_dict, dict):
        x = [float(vetor_ou_dict[c]) for c in carac]
    else:
        x = [float(v) for v in vetor_ou_dict]

    lr = float(mod["learning_rate"])
    soma = float(mod["init_pred"])
    for tree in mod["trees"]:
        node = tree
        while len(node) > 1:
            if x[node[0]] <= node[1]:
                node = node[2]
            else:
                node = node[3]
        soma += lr * node[0]
    return soma


def prever_dias(vetor_ou_dict: list[float] | dict[str, Any], modelo: dict[str, Any] | None = None) -> int:
    dias = int(round(prever_vetor(vetor_ou_dict, modelo)))
    return max(1, dias)


def calcular_predicao_cliente(
    historico_cliente: list[dict[str, Any]],
    novo_pedido: dict[str, Any],
    mediana_global: float | None = None,
) -> tuple[int, datetime]:
    """
    Calcula (dias_previstos, data_previsao) para `novo_pedido` considerando o histórico
    de compras do mesmo cliente e o modelo GradientBoosting treinado.
    """
    mod = carregar_modelo()
    mediana = float(mediana_global if mediana_global is not None else mod.get("median_dias_desde_ultima", 29.0))

    cliente_id = str(novo_pedido.get("id_cliente") or novo_pedido.get("cliente") or "").strip()
    data_alvo = parse_data(novo_pedido.get("data") or novo_pedido.get("data_compra"))
    animal = novo_pedido.get("tipo_racao") if novo_pedido.get("tipo_racao") is not None else novo_pedido.get("animal")
    qtd = float(novo_pedido.get("quantidade_kg") if novo_pedido.get("quantidade_kg") is not None else 0.0)

    # Filtra histórico do cliente até a data da compra atual
    registros_cliente: list[dict[str, Any]] = []
    for h in historico_cliente:
        c_hist = str(h.get("id_cliente") or h.get("cliente") or "").strip()
        if c_hist != cliente_id:
            continue
        d_hist = parse_data(h.get("data") or h.get("data_compra"))
        if d_hist <= data_alvo:
            registros_cliente.append({
                "id_cliente": cliente_id,
                "data": d_hist,
                "tipo_racao": h.get("tipo_racao") if h.get("tipo_racao") is not None else h.get("animal"),
                "quantidade_kg": float(h.get("quantidade_kg") if h.get("quantidade_kg") is not None else 0.0),
                "_is_target": False,
            })

    alvo_item = {
        "id_cliente": cliente_id,
        "data": data_alvo,
        "tipo_racao": animal,
        "quantidade_kg": qtd,
        "_is_target": True,
    }
    registros_cliente.append(alvo_item)

    enriquecidos, _ = construir_features_registros(registros_cliente, mediana_padrao=mediana)
    alvos = [r for r in enriquecidos if r.get("_is_target")]
    registro_final = alvos[-1] if alvos else enriquecidos[-1]

    dias_previstos = prever_dias(registro_final, mod)
    data_previsao = data_alvo + timedelta(days=dias_previstos)
    return dias_previstos, data_previsao


def executar_pipeline_csv(csv_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Carrega dados_predicoes.csv, calcula features e predições para todos os registros."""
    caminho = Path(csv_path) if csv_path else _CSV_DEFAULT_PATH
    registros_brutos: list[dict[str, Any]] = []
    with open(caminho, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            registros_brutos.append({
                "id_cliente": row["id_cliente"],
                "data": row["data"],
                "tipo_racao": row["tipo_racao"],
                "quantidade_kg": float(row["quantidade_kg"]),
            })

    enriquecidos, _ = construir_features_registros(registros_brutos)
    mod = carregar_modelo()
    for r in enriquecidos:
        dias_prev = prever_dias(r, mod)
        r["dias_previstos"] = dias_prev
        r["data_prevista"] = r["data"] + timedelta(days=dias_prev)
        r["diferenca_dias"] = (
            abs(dias_prev - int(r["dias_ate_proxima"]))
            if r["dias_ate_proxima"] is not None
            else None
        )
    return enriquecidos
