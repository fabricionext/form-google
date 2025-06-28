/**
 * ENUMs TypeScript - Espelham os ENUMs Python da Fase 1.5.2
 * Garantem consistência entre frontend e backend
 */

// FieldType - Espelha app.models.enums.FieldType
export enum FieldType {
  TEXT = 'text',
  EMAIL = 'email',
  NUMBER = 'number',
  DATE = 'date',
  SELECT = 'select',
  MULTISELECT = 'multiselect',
  TEXTAREA = 'textarea',
  CHECKBOX = 'checkbox',
  FILE = 'file',
}

// DocumentStatus - Espelha app.models.enums.DocumentStatus
export enum DocumentStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  ARCHIVED = 'archived',
  DEPRECATED = 'deprecated',
}

// TemplateStatus - Espelha app.models.enums.TemplateStatus
export enum TemplateStatus {
  DRAFT = 'draft',
  REVIEWING = 'reviewing',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

// Helper types para validação
export type FieldTypeValue = keyof typeof FieldType;
export type DocumentStatusValue = keyof typeof DocumentStatus;
export type TemplateStatusValue = keyof typeof TemplateStatus;

// Interfaces para objetos do domínio
export interface TemplateField {
  id?: number;
  name: string;
  label: string;
  type: FieldType;
  required: boolean;
  options?: string[];
  validation?: FieldValidation;
  order: number;
}

export interface Template {
  id?: number;
  name: string;
  description?: string;
  status: TemplateStatus;
  fields: TemplateField[];
  created_at?: string;
  updated_at?: string;
}

export interface Document {
  id?: number;
  template_id: number;
  status: DocumentStatus;
  data: Record<string, any>;
  generated_url?: string;
  created_at?: string;
}

export interface FieldValidation {
  required?: boolean;
  min_length?: number;
  max_length?: number;
  pattern?: string;
  custom_rules?: string[];
}

// Validation functions - Espelham EnumValidator Python
export class EnumValidator {
  static isValidFieldType(value: string): value is FieldType {
    return Object.values(FieldType).includes(value as FieldType);
  }

  static isValidDocumentStatus(value: string): value is DocumentStatus {
    return Object.values(DocumentStatus).includes(value as DocumentStatus);
  }

  static isValidTemplateStatus(value: string): value is TemplateStatus {
    return Object.values(TemplateStatus).includes(value as TemplateStatus);
  }

  static getFieldTypeOptions(): Array<{ value: FieldType; label: string }> {
    return [
      { value: FieldType.TEXT, label: 'Texto' },
      { value: FieldType.EMAIL, label: 'E-mail' },
      { value: FieldType.NUMBER, label: 'Número' },
      { value: FieldType.DATE, label: 'Data' },
      { value: FieldType.SELECT, label: 'Seleção' },
      { value: FieldType.MULTISELECT, label: 'Seleção Múltipla' },
      { value: FieldType.TEXTAREA, label: 'Área de Texto' },
      { value: FieldType.CHECKBOX, label: 'Checkbox' },
      { value: FieldType.FILE, label: 'Arquivo' },
    ];
  }

  static getTemplateStatusOptions(): Array<{
    value: TemplateStatus;
    label: string;
  }> {
    return [
      { value: TemplateStatus.DRAFT, label: 'Rascunho' },
      { value: TemplateStatus.REVIEWING, label: 'Em Revisão' },
      { value: TemplateStatus.PUBLISHED, label: 'Publicado' },
      { value: TemplateStatus.ARCHIVED, label: 'Arquivado' },
    ];
  }

  static canTransitionStatus(
    from: TemplateStatus,
    to: TemplateStatus
  ): boolean {
    const validTransitions: Record<TemplateStatus, TemplateStatus[]> = {
      [TemplateStatus.DRAFT]: [TemplateStatus.REVIEWING],
      [TemplateStatus.REVIEWING]: [
        TemplateStatus.PUBLISHED,
        TemplateStatus.ARCHIVED,
      ],
      [TemplateStatus.PUBLISHED]: [TemplateStatus.ARCHIVED],
      [TemplateStatus.ARCHIVED]: [],
    };

    return validTransitions[from]?.includes(to) ?? false;
  }

  static getValidTransitions(currentStatus: TemplateStatus): TemplateStatus[] {
    const validTransitions: Record<TemplateStatus, TemplateStatus[]> = {
      [TemplateStatus.DRAFT]: [TemplateStatus.REVIEWING],
      [TemplateStatus.REVIEWING]: [
        TemplateStatus.PUBLISHED,
        TemplateStatus.ARCHIVED,
      ],
      [TemplateStatus.PUBLISHED]: [TemplateStatus.ARCHIVED],
      [TemplateStatus.ARCHIVED]: [],
    };

    return validTransitions[currentStatus] ?? [];
  }
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  errors?: Record<string, string[]>;
}

export interface TemplateListResponse {
  templates: Template[];
  total: number;
  page: number;
  per_page: number;
}

export interface ValidationResponse {
  valid: boolean;
  errors: Record<string, string[]>;
}
