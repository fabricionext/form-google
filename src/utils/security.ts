/**
 * Utilitários de segurança para validação e sanitização
 */

// Padrões de validação
const VALIDATION_PATTERNS = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  cpf: /^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$/,
  cnpj: /^\d{2}\.?\d{3}\.?\d{3}\/?\d{4}-?\d{2}$/,
  telefone: /^(\(?\d{2}\)?\s?)?(\d{4,5})-?(\d{4})$/,
  cep: /^\d{5}-?\d{3}$/,
  url: /^https?:\/\/.+/,
  sqlInjection: /(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT|'|;|--|\/\*|\*\/)/i,
  xss: /<[^>]*>?/,
  fileName: /^[a-zA-Z0-9._-]+$/
} as const

// Caracteres perigosos
const DANGEROUS_CHARS = ['<', '>', '"', "'", '&', ';', '--', '/*', '*/', 'eval(', 'javascript:']

/**
 * Sanitiza entrada do usuário removendo caracteres perigosos
 */
export function sanitizeInput(input: string): string {
  if (!input || typeof input !== 'string') return ''
  
  let sanitized = input.trim()
  
  // Remover caracteres de controle
  sanitized = sanitized.replace(/[\x00-\x1F\x7F]/g, '')
  
  // Escapar caracteres HTML
  sanitized = sanitized
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
  
  return sanitized
}

/**
 * Remove tags HTML de uma string
 */
export function stripHtml(input: string): string {
  if (!input) return ''
  return input.replace(/<[^>]*>/g, '')
}

/**
 * Valida se o input contém tentativas de injeção SQL
 */
export function hasSqlInjection(input: string): boolean {
  if (!input) return false
  return VALIDATION_PATTERNS.sqlInjection.test(input)
}

/**
 * Valida se o input contém tentativas de XSS
 */
export function hasXss(input: string): boolean {
  if (!input) return false
  
  // Verificar tags HTML suspeitas
  if (VALIDATION_PATTERNS.xss.test(input)) return true
  
  // Verificar javascript: urls
  if (input.toLowerCase().includes('javascript:')) return true
  
  // Verificar event handlers
  const eventHandlers = ['onload', 'onerror', 'onclick', 'onmouseover', 'onfocus']
  return eventHandlers.some(handler => input.toLowerCase().includes(handler))
}

/**
 * Valida entrada do formulário
 */
export function validateFormInput(value: string, type: string): {
  isValid: boolean
  error?: string
  sanitized: string
} {
  if (!value) {
    return { isValid: true, sanitized: '' }
  }
  
  // Verificar ataques
  if (hasSqlInjection(value)) {
    return {
      isValid: false,
      error: 'Entrada contém caracteres não permitidos',
      sanitized: sanitizeInput(value)
    }
  }
  
  if (hasXss(value)) {
    return {
      isValid: false,
      error: 'Entrada contém código não permitido',
      sanitized: sanitizeInput(value)
    }
  }
  
  const sanitized = sanitizeInput(value)
  
  // Validações específicas por tipo
  switch (type) {
    case 'email':
      if (!VALIDATION_PATTERNS.email.test(sanitized)) {
        return {
          isValid: false,
          error: 'Formato de email inválido',
          sanitized
        }
      }
      break
      
    case 'cpf':
      if (!isValidCPF(sanitized)) {
        return {
          isValid: false,
          error: 'CPF inválido',
          sanitized
        }
      }
      break
      
    case 'cnpj':
      if (!isValidCNPJ(sanitized)) {
        return {
          isValid: false,
          error: 'CNPJ inválido',
          sanitized
        }
      }
      break
      
    case 'telefone':
      if (!VALIDATION_PATTERNS.telefone.test(sanitized.replace(/\D/g, ''))) {
        return {
          isValid: false,
          error: 'Formato de telefone inválido',
          sanitized
        }
      }
      break
      
    case 'cep':
      if (!VALIDATION_PATTERNS.cep.test(sanitized.replace(/\D/g, ''))) {
        return {
          isValid: false,
          error: 'Formato de CEP inválido',
          sanitized
        }
      }
      break
  }
  
  return { isValid: true, sanitized }
}

/**
 * Validação de CPF
 */
export function isValidCPF(cpf: string): boolean {
  if (!cpf) return false
  
  const numbers = cpf.replace(/\D/g, '')
  if (numbers.length !== 11) return false
  
  // Verificar se todos os dígitos são iguais
  if (/^(\d)\1{10}$/.test(numbers)) return false
  
  // Validar dígitos verificadores
  let sum = 0
  for (let i = 0; i < 9; i++) {
    sum += parseInt(numbers[i]) * (10 - i)
  }
  
  let remainder = sum % 11
  const digit1 = remainder < 2 ? 0 : 11 - remainder
  
  if (parseInt(numbers[9]) !== digit1) return false
  
  sum = 0
  for (let i = 0; i < 10; i++) {
    sum += parseInt(numbers[i]) * (11 - i)
  }
  
  remainder = sum % 11
  const digit2 = remainder < 2 ? 0 : 11 - remainder
  
  return parseInt(numbers[10]) === digit2
}

/**
 * Validação de CNPJ
 */
export function isValidCNPJ(cnpj: string): boolean {
  if (!cnpj) return false
  
  const numbers = cnpj.replace(/\D/g, '')
  if (numbers.length !== 14) return false
  
  // Verificar se todos os dígitos são iguais
  if (/^(\d)\1{13}$/.test(numbers)) return false
  
  // Validar primeiro dígito verificador
  const weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  let sum = 0
  
  for (let i = 0; i < 12; i++) {
    sum += parseInt(numbers[i]) * weights1[i]
  }
  
  let remainder = sum % 11
  const digit1 = remainder < 2 ? 0 : 11 - remainder
  
  if (parseInt(numbers[12]) !== digit1) return false
  
  // Validar segundo dígito verificador
  const weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  sum = 0
  
  for (let i = 0; i < 13; i++) {
    sum += parseInt(numbers[i]) * weights2[i]
  }
  
  remainder = sum % 11
  const digit2 = remainder < 2 ? 0 : 11 - remainder
  
  return parseInt(numbers[13]) === digit2
}

/**
 * Gera um token CSRF simples
 */
export function generateCSRFToken(): string {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

/**
 * Valida token CSRF
 */
export function validateCSRFToken(token: string, expected: string): boolean {
  if (!token || !expected) return false
  return token === expected
}

/**
 * Rate limiting simples no client-side
 */
class RateLimiter {
  private requests: Map<string, number[]> = new Map()
  
  isAllowed(key: string, maxRequests: number = 10, windowMs: number = 60000): boolean {
    const now = Date.now()
    const windowStart = now - windowMs
    
    if (!this.requests.has(key)) {
      this.requests.set(key, [])
    }
    
    const requests = this.requests.get(key)!
    
    // Remover requisições antigas
    const validRequests = requests.filter(time => time > windowStart)
    
    if (validRequests.length >= maxRequests) {
      return false
    }
    
    validRequests.push(now)
    this.requests.set(key, validRequests)
    
    return true
  }
  
  clear(key: string): void {
    this.requests.delete(key)
  }
}

export const rateLimiter = new RateLimiter()

/**
 * Validação de entrada de arquivo
 */
export function validateFileInput(file: File, allowedTypes: string[] = [], maxSize: number = 5 * 1024 * 1024): {
  isValid: boolean
  error?: string
} {
  if (!file) {
    return { isValid: false, error: 'Nenhum arquivo selecionado' }
  }
  
  // Verificar tamanho
  if (file.size > maxSize) {
    return {
      isValid: false,
      error: `Arquivo muito grande. Máximo permitido: ${(maxSize / 1024 / 1024).toFixed(1)}MB`
    }
  }
  
  // Verificar tipo
  if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
    return {
      isValid: false,
      error: `Tipo de arquivo não permitido. Tipos aceitos: ${allowedTypes.join(', ')}`
    }
  }
  
  // Verificar nome do arquivo
  if (!VALIDATION_PATTERNS.fileName.test(file.name)) {
    return {
      isValid: false,
      error: 'Nome do arquivo contém caracteres não permitidos'
    }
  }
  
  return { isValid: true }
}

/**
 * Codifica dados para transmissão segura
 */
export function encodeForTransmission(data: any): string {
  try {
    return btoa(JSON.stringify(data))
  } catch (error) {
    throw new Error('Erro ao codificar dados para transmissão')
  }
}

/**
 * Decodifica dados recebidos
 */
export function decodeFromTransmission(encoded: string): any {
  try {
    return JSON.parse(atob(encoded))
  } catch (error) {
    throw new Error('Erro ao decodificar dados recebidos')
  }
}

/**
 * Classe para logging seguro
 */
export class SecureLogger {
  private static sensitiveFields = [
    'password', 'senha', 'cpf', 'cnpj', 'token', 'csrf',
    'api_key', 'secret', 'credit_card', 'cartao'
  ]
  
  static sanitizeForLog(data: any): any {
    if (typeof data !== 'object' || data === null) {
      return data
    }
    
    const sanitized = { ...data }
    
    for (const key in sanitized) {
      if (this.sensitiveFields.some(field => 
        key.toLowerCase().includes(field.toLowerCase())
      )) {
        sanitized[key] = '[REDACTED]'
      } else if (typeof sanitized[key] === 'object') {
        sanitized[key] = this.sanitizeForLog(sanitized[key])
      }
    }
    
    return sanitized
  }
  
  static log(level: 'info' | 'warn' | 'error', message: string, data?: any): void {
    const sanitizedData = data ? this.sanitizeForLog(data) : undefined
    
    switch (level) {
      case 'info':
        console.info(`[INFO] ${message}`, sanitizedData)
        break
      case 'warn':
        console.warn(`[WARN] ${message}`, sanitizedData)
        break
      case 'error':
        console.error(`[ERROR] ${message}`, sanitizedData)
        break
    }
  }
}