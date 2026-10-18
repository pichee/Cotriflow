from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from .models import TipoUsuario, StatusPedido
from .validators import normalize_document, normalize_email


class UsuarioBase(BaseModel):
    nome: str
    documento: str | None = None
    email: EmailStr
    tipo_usuario: TipoUsuario = TipoUsuario.VENDEDOR
    ativo: bool = True

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

class UsuarioCreate(UsuarioBase):
    senha: str = Field(min_length=6)

    @field_validator("documento")
    @classmethod
    def validate_documento(cls, value: str | None) -> str | None:
        return normalize_document(value)

class UsuarioUpdate(BaseModel):
    nome: str | None = None
    documento: str | None = None
    email: EmailStr | None = None
    tipo_usuario: TipoUsuario | None = None
    ativo: bool | None = None
    senha: str | None = Field(default=None, min_length=6)

    @field_validator("documento")
    @classmethod
    def validate_documento(cls, value: str | None) -> str | None:
        return normalize_document(value)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalize_email(value)

class UsuarioOut(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)
    id_usuario: int

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class ClienteBase(BaseModel):
    nome: str
    documento: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    observacoes: str | None = None

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalize_email(value)
class ClienteCreate(ClienteBase):
    @field_validator("documento")
    @classmethod
    def validate_documento(cls, value: str | None) -> str | None:
        return normalize_document(value)

class ClienteUpdate(BaseModel):
    nome: str | None = None
    documento: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    observacoes: str | None = None

    @field_validator("documento")
    @classmethod
    def validate_documento(cls, value: str | None) -> str | None:
        return normalize_document(value)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return normalize_email(value)
class ClienteOut(ClienteBase):
    model_config = ConfigDict(from_attributes=True)
    id_cliente: int


class PropriedadeBase(BaseModel):
    nome: str
    localizacao: str
    id_cliente: int
class PropriedadeCreate(PropriedadeBase): pass
class PropriedadeUpdate(BaseModel):
    nome: str | None = None
    localizacao: str | None = None
    id_cliente: int | None = None
class PropriedadeOut(PropriedadeBase):
    model_config = ConfigDict(from_attributes=True)
    id_propriedade: int


class ProdutoBase(BaseModel):
    nome: str
    tipo: str
    peso_unidade: float = 0
    ativo: bool = True
class ProdutoCreate(ProdutoBase): pass
class ProdutoUpdate(BaseModel):
    nome: str | None = None
    tipo: str | None = None
    peso_unidade: float | None = None
    ativo: bool | None = None
class ProdutoOut(ProdutoBase):
    model_config = ConfigDict(from_attributes=True)
    id_produto: int


class PedidoProduto(BaseModel):
    id_produto: int
    quantidade: float = Field(gt=0)
class PedidoCreate(BaseModel):
    id_cliente: int
    endereco_entrega: str
    produtos: list[PedidoProduto] = Field(default_factory=list)
class PedidoUpdate(BaseModel):
    status: StatusPedido | None = None
    endereco_entrega: str | None = None
    id_cliente: int | None = None
    produtos: list[PedidoProduto] | None = None
class PedidoProdutoOut(BaseModel):
    id_produto: int
    nome: str
    quantidade: float
class PedidoOut(BaseModel):
    id_pedido: int
    data: datetime
    status: StatusPedido
    peso_total: float
    endereco_entrega: str
    id_cliente: int
    cliente_nome: str
    produtos: list[PedidoProdutoOut]


class PredicaoBase(BaseModel):
    cliente: str
    animal: str | None = None
    quantidade_kg: float | None = None
    data_compra: datetime
    dias_previstos: int | None = None
    data_previsao: datetime
    data_real: datetime | None = None
    observacao: str | None = None

class PredicaoCreate(BaseModel):
    cliente: str
    animal: str | None = None
    quantidade_kg: float | None = None
    data_compra: datetime
    dias_previstos: int | None = None
    data_previsao: datetime | None = None
    data_real: datetime | None = None
    observacao: str | None = None

class PredicaoUpdate(BaseModel):
    cliente: str | None = None
    animal: str | None = None
    quantidade_kg: float | None = None
    data_compra: datetime | None = None
    dias_previstos: int | None = None
    data_previsao: datetime | None = None
    data_real: datetime | None = None
    observacao: str | None = None

class PredicaoOut(PredicaoBase):
    model_config = ConfigDict(from_attributes=True)
    id_predicao: int

