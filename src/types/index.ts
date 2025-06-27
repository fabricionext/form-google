/**
 * Tipos TypeScript para o sistema de formulários dinâmicos
 */

// Tipos básicos
export interface Cliente {
  id: number
  tipo_pessoa: 'FISICA' | 'JURIDICA'
  email: string
  telefone_celular?: string
  telefone_outro?: string
  
  // Pessoa Física
  primeiro_nome?: string
  sobrenome?: string
  nome_completo?: string
  cpf?: string
  rg_numero?: string
  rg_orgao_emissor?: string
  rg_uf_emissor?: string
  data_nascimento?: string
  nacionalidade?: string
  estado_civil?: string
  profissao?: string
  cnh_numero?: string
  
  // Endereço
  endereco_logradouro?: string
  endereco_numero?: string
  endereco_complemento?: string
  endereco_bairro?: string
  endereco_cidade?: string
  endereco_estado?: string
  endereco_cep?: string
  
  // Pessoa Jurídica
  razao_social?: string
  cnpj?: string
  representante_nome?: string
  representante_cpf?: string
  representante_rg_numero?: string
  representante_rg_orgao_emissor?: string
  representante_rg_uf_emissor?: string
  representante_cargo?: string
}

export interface AutoridadeTransito {
  id: number
  nome: string
  cnpj?: string
  logradouro?: string
  numero?: string
  complemento?: string
  cidade?: string
  estado?: string
  cep?: string
}

// Tipos de campos do formulário
export type TipoCampo = 
  | 'text' 
  | 'email' 
  | 'tel' 
  | 'date' 
  | 'textarea' 
  | 'select' 
  | 'number' 
  | 'password' 
  | 'url'

export type CategoriaPlaceholder = 
  | 'cliente' 
  | 'endereco' 
  | 'processo' 
  | 'autoridades' 
  | 'polo_ativo' 
  | 'polo_passivo' 
  | 'terceiros' 
  | 'autor_dados' 
  | 'autor_endereco' 
  | 'data' 
  | 'outros'

export interface Campo {
  chave: string
  tipo: TipoCampo
  label: string
  placeholder_text?: string
  obrigatorio: boolean
  categoria?: CategoriaPlaceholder
  opcoes_json?: string
  ordem?: number
  elemento?: HTMLElement
}

// Tipos para organização de campos
export interface AutorData {
  dados: Campo[]
  endereco: Campo[]
}

export interface CamposOrganizados {
  autores: Record<string | number, AutorData>
  cliente: Campo[]
  endereco: Campo[]
  processo: Campo[]
  autoridades: Campo[]
  polo_ativo: Campo[]
  polo_passivo: Campo[]
  terceiros: Campo[]
  outros: Campo[]
}

// Tipos para drag and drop
export interface DragData {
  type: 'cliente' | 'autoridade'
  data: Cliente | AutoridadeTransito
}

export interface DropEvent {
  clienteData?: Cliente
  autoridadeData?: AutoridadeTransito
  autorIndex?: string | number
  index?: string | number
}

// Tipos para formulário
export interface FormData {
  [key: string]: string | number | boolean | null | undefined
}

export interface FormularioState {
  formData: FormData
  clientes: Cliente[]
  autoridades: AutoridadeTransito[]
  campos: Campo[]
  dataChanged: boolean
  submitting: boolean
}

// Tipos para validação
export interface ValidationError {
  field: string
  message: string
  type: 'required' | 'invalid' | 'custom'
}

export interface ValidationResult {
  isValid: boolean
  errors: ValidationError[]
}

// Tipos para busca fuzzy
export interface SearchResult<T> {
  item: T
  score: number
}

// Tipos para API responses
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  errors?: ValidationError[]
  redirect?: string
}

// Tipos para rascunhos
export interface RascunhoData {
  data: FormData
  timestamp: string
}

// Tipos para eventos do formulário
export interface CampoEvent {
  chave: string
  valor: string | number | boolean
}

export interface ClienteDropEvent {
  clienteData: Cliente
  autorIndex?: string | number
}

export interface AutoridadeDropEvent {
  autoridadeData: AutoridadeTransito
  index: string | number
}

// Tipos para composables
export interface DragAndDropState {
  isDragging: boolean
  dragData: DragData | null
}

export interface DragAndDropCallbacks {
  clientDrop?: (cliente: Cliente) => void
  authorDrop?: (event: ClienteDropEvent) => void
  authorityDrop?: (event: AutoridadeDropEvent) => void
}

// Tipos para configuração
export interface FormularioConfig {
  autoSaveInterval: number
  maxSearchResults: number
  searchThreshold: number
  validationEnabled: boolean
  debugMode: boolean
}

// Tipos para máscaras de input
export type MascaraTipo = 'cpf' | 'cnpj' | 'telefone' | 'cep' | 'rg' | 'cnh'

export interface MascaraConfig {
  tipo: MascaraTipo
  pattern: string
  placeholder: string
  maxLength: number
}

// Tipos para análise de personas (integração com backend)
export interface PersonaAnalise {
  id: number
  modelo_id: number
  documento_id: string
  personas_detectadas: Record<string, number>
  patterns_detectados: string[]
  total_placeholders: number
  total_personas: number
  sugestoes: string[]
  criado_em: string
}

// Tipos para modelos de petição
export interface PeticaoModelo {
  id: number
  nome: string
  slug: string
  google_doc_id: string
  pasta_destino_id: string
  descricao?: string
  ativo: boolean
  total_placeholders: number
  total_personas: number
  ultima_sincronizacao?: string
  criado_em: string
  atualizado_em: string
}

// Export de tipos utilitários
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>
export type Nullable<T> = T | null
export type AsyncData<T> = Promise<T>

// Tipos para integração com Vue
export type ComponentEmits = Record<string, any>
export type ComponentProps = Record<string, any>