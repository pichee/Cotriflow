from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from .database import SessionLocal
from .dominio import Predicao, PredicaoDominio
from .features import (
    calcular_predicao_cliente,
    carregar_modelo,
    construir_features_registros,
    normalizar_racao,
    parse_data,
    prever_dias,
)

logger = logging.getLogger(__name__)


def buscaPedidos(db: Session) -> list[dict[str, Any]]:
    """Coleta o histórico de compras de todos os clientes na tabela de predições."""
    registros = (
        db.query(Predicao)
        .order_by(Predicao.cliente.asc(), Predicao.data_compra.asc(), Predicao.id_predicao.asc())
        .all()
    )
    resultado: list[dict[str, Any]] = []
    for r in registros:
        resultado.append({
            "id_predicao": r.id_predicao,
            "id_cliente": r.cliente,
            "cliente": r.cliente,
            "data": r.data_compra,
            "data_compra": r.data_compra,
            "tipo_racao": r.animal,
            "animal": r.animal,
            "quantidade_kg": r.quantidade_kg if r.quantidade_kg is not None else 0.0,
            "obj": r,
        })
    return resultado


def executaAlgoritmo(
    historico_cliente: list[dict[str, Any]],
    pedido_atual: dict[str, Any] | None = None,
    mediana_global: float | None = None,
) -> dict[str, Any]:
    """
    Executa o algoritmo preditivo (GradientBoosting + engenharia de features de features.py)
    para um cliente específico ou para seu pedido mais recente.
    """
    if pedido_atual is not None:
        dias_prev, data_prev = calcular_predicao_cliente(
            historico_cliente=historico_cliente,
            novo_pedido=pedido_atual,
            mediana_global=mediana_global,
        )
        return {
            "dias_previstos": dias_prev,
            "data_previsao": data_prev,
        }

    if not historico_cliente:
        raise ValueError("Histórico do cliente está vazio.")

    mod = carregar_modelo()
    mediana = float(mediana_global if mediana_global is not None else mod.get("median_dias_desde_ultima", 29.0))
    enriquecidos, _ = construir_features_registros(historico_cliente, mediana_padrao=mediana)
    for item in enriquecidos:
        dias_prev = prever_dias(item, mod)
        item["dias_previstos"] = dias_prev
        item["data_previsao"] = item["data"] + timedelta(days=dias_prev)
    return {
        "registros": enriquecidos,
        "dias_previstos": enriquecidos[-1]["dias_previstos"],
        "data_previsao": enriquecidos[-1]["data_previsao"],
    }


def criaPredicao(db: Session, dados_predicao: dict[str, Any], commit: bool = True) -> Predicao:
    """Instancia e persiste o resultado na tabela/classe Predicao."""
    animal_raw = dados_predicao.get("animal") or dados_predicao.get("tipo_racao")
    animal_norm = normalizar_racao(animal_raw) if animal_raw else None
    data_compra = parse_data(dados_predicao["data_compra"])
    dias_previstos = int(dados_predicao["dias_previstos"])
    data_previsao = dados_predicao.get("data_previsao") or (data_compra + timedelta(days=dias_previstos))

    dom = PredicaoDominio(
        cliente=str(dados_predicao["cliente"]).strip(),
        animal=animal_norm or animal_raw,
        quantidade_kg=dados_predicao.get("quantidade_kg"),
        data_compra=data_compra,
        dias_previstos=dias_previstos,
        data_previsao=data_previsao,
        data_real=dados_predicao.get("data_real"),
        observacao=dados_predicao.get("observacao"),
    )
    obj = dom.to_orm()
    db.add(obj)
    if commit:
        db.commit()
        db.refresh(obj)
    return obj


def iniciaPredicao(db: Session | None = None) -> list[Predicao]:
    """
    Executa o processamento das predições de todos os clientes com resiliência (RNF03):
    caso falhe para um cliente específico, o processamento dos demais não é interrompido.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        todos_pedidos = buscaPedidos(db)
        if not todos_pedidos:
            return []

        por_cliente: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for p in todos_pedidos:
            por_cliente[p["id_cliente"]].append(p)

        # Calcula a mediana global de dias_desde_ultima em toda a base
        intervalos: list[float] = []
        for _, lista in por_cliente.items():
            lista_ord = sorted(lista, key=lambda x: (parse_data(x["data"]), x.get("id_predicao") or 0))
            for i in range(1, len(lista_ord)):
                d_atual = parse_data(lista_ord[i]["data"])
                d_ant = parse_data(lista_ord[i - 1]["data"])
                intervalos.append(float((d_atual - d_ant).days))

        mod = carregar_modelo()
        mediana_global = (
            float(statistics.median(intervalos))
            if intervalos
            else float(mod.get("median_dias_desde_ultima", 29.0))
        )

        atualizados: list[Predicao] = []
        for cliente_id, lista_cliente in por_cliente.items():
            try:
                resultado = executaAlgoritmo(lista_cliente, mediana_global=mediana_global)
                for item in resultado["registros"]:
                    obj: Predicao | None = item.get("obj")
                    if obj is not None:
                        obj.dias_previstos = item["dias_previstos"]
                        obj.data_previsao = item["data_prevista"] if "data_prevista" in item else item["data_previsao"]
                        obj.data_real = item["proxima_data"]
                        if not obj.observacao and obj.animal:
                            obj.observacao = f"Previsão calculada com base no consumo de {obj.animal}."
                        atualizados.append(obj)
            except Exception as exc:
                # RNF03: Resiliência — falha em um cliente não interrompe os demais
                logger.warning("Falha ao processar predição para cliente %s: %s", cliente_id, exc)
                continue

        db.commit()
        return atualizados
    finally:
        if close_db:
            db.close()
