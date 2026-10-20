from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class TipoUsuario(str, Enum):
    ADMIN = "ADMIN"
    VENDEDOR = "VENDEDOR"


class StatusPedido(str, Enum):
    PENDENTE = "PENDENTE"
    SEPARANDO = "SEPARANDO"
    EM_ENTREGA = "EM_ENTREGA"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"


pedido_produto = Table(
    "pedido_produto",
    Base.metadata,
    Column("pedido_id", ForeignKey("pedidos.id_pedido", ondelete="CASCADE"), primary_key=True),
    Column("produto_id", ForeignKey("produtos.id_produto", ondelete="RESTRICT"), primary_key=True, index=True),
    Column("quantidade", Float, nullable=False, default=1),
    CheckConstraint("quantidade > 0", name="ck_pedido_produto_quantidade_positiva"),
)


class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    documento: Mapped[str | None] = mapped_column(String(30), unique=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_usuario: Mapped[TipoUsuario] = mapped_column(nullable=False, default=TipoUsuario.VENDEDOR, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TokenRevogado(Base):
    __tablename__ = "tokens_revogados"
    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class Cliente(Base):
    __tablename__ = "clientes"
    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    documento: Mapped[str | None] = mapped_column(String(30), unique=True)
    telefone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(160))
    observacoes: Mapped[str | None] = mapped_column(Text)
    propriedades: Mapped[list["Propriedade"]] = relationship(back_populates="cliente", cascade="all, delete-orphan")
    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="cliente")


class Propriedade(Base):
    __tablename__ = "propriedades"
    id_propriedade: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    localizacao: Mapped[str] = mapped_column(String(255), nullable=False)
    id_cliente: Mapped[int] = mapped_column(
        ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False, index=True
    )
    cliente: Mapped[Cliente] = relationship(back_populates="propriedades")


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (
        CheckConstraint("peso_unidade >= 0", name="ck_produtos_peso_nao_negativo"),
    )
    id_produto: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    peso_unidade: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pedidos: Mapped[list["Pedido"]] = relationship(secondary=pedido_produto, back_populates="produtos")


class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = (
        CheckConstraint("peso_total >= 0", name="ck_pedidos_peso_total_nao_negativo"),
        Index("ix_pedidos_cliente_data", "id_cliente", "data"),
    )
    id_pedido: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, index=True)
    status: Mapped[StatusPedido] = mapped_column(nullable=False, default=StatusPedido.PENDENTE, index=True)
    peso_total: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    endereco_entrega: Mapped[str] = mapped_column(String(255), nullable=False)
    id_cliente: Mapped[int] = mapped_column(
        ForeignKey("clientes.id_cliente", ondelete="RESTRICT"), nullable=False, index=True
    )
    cliente: Mapped[Cliente] = relationship(back_populates="pedidos")
    produtos: Mapped[list[Produto]] = relationship(secondary=pedido_produto, back_populates="pedidos")


class Predicao(Base):
    __tablename__ = "predicoes"
    __table_args__ = (
        Index("ix_predicoes_cliente_data_id", "cliente", "data_compra", "id_predicao"),
    )
    id_predicao: Mapped[int] = mapped_column(primary_key=True)
    cliente: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    animal: Mapped[str | None] = mapped_column(String(80))
    quantidade_kg: Mapped[float | None] = mapped_column(Float)
    data_compra: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    dias_previstos: Mapped[int | None] = mapped_column(Integer)
    data_previsao: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    data_real: Mapped[datetime | None] = mapped_column(DateTime)
    observacao: Mapped[str | None] = mapped_column(Text)
