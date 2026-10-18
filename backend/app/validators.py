import re


def normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().lower()


def _only_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _has_repeated_digits(value: str) -> bool:
    return len(set(value)) == 1


def is_valid_cpf(value: str) -> bool:
    digits = _only_digits(value)
    if len(digits) != 11 or _has_repeated_digits(digits):
        return False

    first_sum = sum(int(digits[index]) * (10 - index) for index in range(9))
    first_digit = (first_sum * 10 % 11) % 10
    if first_digit != int(digits[9]):
        return False

    second_sum = sum(int(digits[index]) * (11 - index) for index in range(10))
    second_digit = (second_sum * 10 % 11) % 10
    return second_digit == int(digits[10])


def is_valid_cnpj(value: str) -> bool:
    digits = _only_digits(value)
    if len(digits) != 14 or _has_repeated_digits(digits):
        return False

    def calculate_digit(base: str, weights: tuple[int, ...]) -> int:
        total = sum(int(digit) * weight for digit, weight in zip(base, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    first_digit = calculate_digit(digits[:12], (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    if first_digit != int(digits[12]):
        return False

    second_digit = calculate_digit(digits[:13], (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2))
    return second_digit == int(digits[13])


def normalize_document(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None

    if not re.fullmatch(r"[\d.\-/\s]+", value):
        raise ValueError("CPF ou CNPJ inválido")

    digits = _only_digits(value)
    if len(digits) == 11 and is_valid_cpf(digits):
        return digits
    if len(digits) == 14 and is_valid_cnpj(digits):
        return digits
    raise ValueError("CPF ou CNPJ inválido")
