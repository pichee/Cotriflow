const onlyDigits = value => String(value ?? '').replace(/\D/g, '')

const hasRepeatedDigits = value => new Set(value).size === 1

export function isValidCpf(value) {
  const digits = onlyDigits(value)
  if (digits.length !== 11 || hasRepeatedDigits(digits)) return false

  const firstSum = digits
    .slice(0, 9)
    .split('')
    .reduce((total, digit, index) => total + Number(digit) * (10 - index), 0)
  const firstDigit = (firstSum * 10 % 11) % 10
  if (firstDigit !== Number(digits[9])) return false

  const secondSum = digits
    .slice(0, 10)
    .split('')
    .reduce((total, digit, index) => total + Number(digit) * (11 - index), 0)
  const secondDigit = (secondSum * 10 % 11) % 10
  return secondDigit === Number(digits[10])
}

export function isValidCnpj(value) {
  const digits = onlyDigits(value)
  if (digits.length !== 14 || hasRepeatedDigits(digits)) return false

  function calculateDigit(base, weights) {
    const total = base
      .split('')
      .reduce((sum, digit, index) => sum + Number(digit) * weights[index], 0)
    const remainder = total % 11
    return remainder < 2 ? 0 : 11 - remainder
  }

  const firstDigit = calculateDigit(digits.slice(0, 12), [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
  if (firstDigit !== Number(digits[12])) return false

  const secondDigit = calculateDigit(digits.slice(0, 13), [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
  return secondDigit === Number(digits[13])
}

export function isValidDocument(value) {
  const raw = String(value ?? '').trim()
  if (!raw || !/^[\d.\-/\s]+$/.test(raw)) return false
  const digits = onlyDigits(raw)
  return digits.length === 11 ? isValidCpf(digits) : isValidCnpj(digits)
}

export function normalizeDocument(value) {
  return onlyDigits(value)
}

export function normalizeEmail(value) {
  return String(value ?? '').trim().toLowerCase()
}

export function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizeEmail(value))
}
