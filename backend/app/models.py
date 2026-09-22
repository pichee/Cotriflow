from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Table, Column, Text, func
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
    Column("produto_id", ForeignKey("produtos.id_produto", ondelete="RESTRICT"), primary_key=True),
    Column("quantidade", Float, nullable=False, default=1),
)


class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(30), unique=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_usuario: Mapped[TipoUsuario] = mapped_column(nullable=False, default=TipoUsuario.VENDEDOR)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TokenRevogado(Base):
    __tablename__ = "tokens_revogados"
    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expira_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Cliente(Base):
    __tablename__ = "clientes"
    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(30), unique=True)
    telefone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(160))
    observacoes: Mapped[str | None] = mapped_column(Text)
    propriedades: Mapped[list["Propriedade"]] = relationship(back_populates="cliente", cascade="all, delete-orphan")
    pedidos: Mapped[list["Pedido"]] = relationship(back_populates="cliente")


class Propriedade(Base):
    __tablename__ = "propriedades"
    id_propriedade: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    localizacao: Mapped[str] = mapped_column(String(255), nullable=False)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("clientes.id_cliente", ondelete="CASCADE"), nullable=False)
    cliente: Mapped[Cliente] = relationship(back_populates="propriedades")


class Produto(Base):
    __tablename__ = "produtos"
    id_produto: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    tipo: Mapped[str] = mapped_column(String(80), nullable=False)
    peso_unidade: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pedidos: Mapped[list["Pedido"]] = relationship(secondary=pedido_produto, back_populates="produtos")


class Pedido(Base):
    __tablename__ = "pedidos"
    id_pedido: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    status: Mapped[StatusPedido] = mapped_column(nullable=False, default=StatusPedido.PENDENTE)
    peso_total: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    endereco_entrega: Mapped[str] = mapped_column(String(255), nullable=False)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("clientes.id_cliente", ondelete="RESTRICT"), nullable=False)
    cliente: Mapped[Cliente] = relationship(back_populates="pedidos")
    produtos: Mapped[list[Produto]] = relationship(secondary=pedido_produto, back_populates="pedidos")


class Predicao(Base):
    __tablename__ = "predicoes"
    id_predicao: Mapped[int] = mapped_column(primary_key=True)
    data_predicao: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    cliente: Mapped[str] = mapped_column(String(160), nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text)
