import unittest

from app.validators import is_valid_cnpj, is_valid_cpf, normalize_document

try:
    from pydantic import ValidationError
    from app.schemas import ClienteCreate, ClienteOut, UsuarioCreate
    SCHEMA_DEPENDENCIES_AVAILABLE = True
except ModuleNotFoundError:
    SCHEMA_DEPENDENCIES_AVAILABLE = False


class DocumentValidatorTests(unittest.TestCase):
    def test_accepts_and_normalizes_valid_cpf(self):
        self.assertTrue(is_valid_cpf("529.982.247-25"))
        self.assertEqual(normalize_document("529.982.247-25"), "52998224725")

    def test_rejects_invalid_cpf(self):
        self.assertFalse(is_valid_cpf("529.982.247-24"))
        self.assertFalse(is_valid_cpf("111.111.111-11"))
        with self.assertRaisesRegex(ValueError, "CPF ou CNPJ inválido"):
            normalize_document("529.982.247-24")
        with self.assertRaisesRegex(ValueError, "CPF ou CNPJ inválido"):
            normalize_document("abc529.982.247-25")

    def test_accepts_and_normalizes_valid_cnpj(self):
        self.assertTrue(is_valid_cnpj("04.252.011/0001-10"))
        self.assertEqual(normalize_document("04.252.011/0001-10"), "04252011000110")

    def test_rejects_invalid_cnpj(self):
        self.assertFalse(is_valid_cnpj("04.252.011/0001-11"))
        self.assertFalse(is_valid_cnpj("00.000.000/0000-00"))
        with self.assertRaisesRegex(ValueError, "CPF ou CNPJ inválido"):
            normalize_document("04.252.011/0001-11")

    def test_empty_document_is_optional(self):
        self.assertIsNone(normalize_document(None))
        self.assertIsNone(normalize_document("  "))


@unittest.skipUnless(SCHEMA_DEPENDENCIES_AVAILABLE, "Dependências do backend não instaladas")
class SchemaValidationTests(unittest.TestCase):
    def test_user_normalizes_document_and_email(self):
        user = UsuarioCreate(
            nome="Maria",
            documento="529.982.247-25",
            email="  MARIA@EXAMPLE.COM  ",
            senha="123456",
        )
        self.assertEqual(user.documento, "52998224725")
        self.assertEqual(str(user.email), "maria@example.com")

    def test_client_rejects_invalid_document(self):
        with self.assertRaises(ValidationError):
            ClienteCreate(nome="Cliente", documento="123", email="cliente@example.com")

    def test_client_rejects_invalid_email(self):
        with self.assertRaises(ValidationError):
            ClienteCreate(nome="Cliente", documento="52998224725", email="email-invalido")

    def test_output_keeps_legacy_document_readable(self):
        client = ClienteOut(id_cliente=1, nome="Cliente antigo", documento="documento legado")
        self.assertEqual(client.documento, "documento legado")


if __name__ == "__main__":
    unittest.main()
