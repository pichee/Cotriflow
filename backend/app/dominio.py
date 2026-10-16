from __future__ import annotations

from datetime import datetime
from typing import Any
from .models import Cliente, Pedido, Predicao, Produto, Propriedade, Usuario


class PredicaoDominio:
    """Representação de domínio para o cálculo e persistência de predições."""

    def __init__(
        self,
        cliente: str,
        data_compra: datetime,
        dias_previstos: int,
        data_previsao: datetime,
        animal: str | None = None,
        quantidade_kg: float | None = None,
        data_real: datetime | None = None,
        observacao: str | None = None,
    ) -> None:
        self.cliente = cliente
        self.animal = animal
        self.quantidade_kg = quantidade_kg
        self.data_compra = data_compra
        self.dias_previstos = dias_previstos
        self.data_previsao = data_previsao
        self.data_real = data_real
        self.observacao = observacao or (
            f"Previsão calculada com base no consumo de {animal}."
            if animal
            else "Previsão calculada pelo modelo preditivo."
        )

    def to_orm(self) -> Predicao:
        return Predicao(
            cliente=self.cliente,
            animal=self.animal,
            quantidade_kg=self.quantidade_kg,
            data_compra=self.data_compra,
            dias_previstos=self.dias_previstos,
            data_previsao=self.data_previsao,
            data_real=self.data_real,
            observacao=self.observacao,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "cliente": self.cliente,
            "animal": self.animal,
            "quantidade_kg": self.quantidade_kg,
            "data_compra": self.data_compra,
            "dias_previstos": self.dias_previstos,
            "data_previsao": self.data_previsao,
            "data_real": self.data_real,
            "observacao": self.observacao,
        }


__all__ = [
    "Cliente",
    "Pedido",
    "Predicao",
    "PredicaoDominio",
    "Produto",
    "Propriedade",
    "Usuario",
]
