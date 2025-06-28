import { describe, it, expect } from 'vitest';
import {
  FieldType,
  DocumentStatus,
  TemplateStatus,
  EnumValidator,
} from '@/types/enums';

describe('ENUMs TypeScript - Consistência com Python Fase 1.5.2', () => {
  describe('FieldType Enum', () => {
    it('should have exactly the same values as Python FieldType', () => {
      // Given: Expected values from Python app.models.enums.FieldType
      const expectedValues = [
        'text',
        'email',
        'number',
        'date',
        'select',
        'multiselect',
        'textarea',
        'checkbox',
        'file',
      ];

      // When: Get TypeScript enum values
      const tsValues = Object.values(FieldType);

      // Then: Should match exactly
      expect(tsValues).toEqual(expectedValues);
      expect(tsValues).toHaveLength(9);
    });

    it('should validate field types correctly', () => {
      // Valid field types
      expect(EnumValidator.isValidFieldType('text')).toBe(true);
      expect(EnumValidator.isValidFieldType('email')).toBe(true);
      expect(EnumValidator.isValidFieldType('select')).toBe(true);

      // Invalid field types
      expect(EnumValidator.isValidFieldType('invalid')).toBe(false);
      expect(EnumValidator.isValidFieldType('')).toBe(false);
      expect(EnumValidator.isValidFieldType('TEXT')).toBe(false); // Case sensitive
    });
  });

  describe('TemplateStatus Enum', () => {
    it('should have exactly the same values as Python TemplateStatus', () => {
      // Given: Expected values from Python app.models.enums.TemplateStatus
      const expectedValues = ['draft', 'reviewing', 'published', 'archived'];

      // When: Get TypeScript enum values
      const tsValues = Object.values(TemplateStatus);

      // Then: Should match exactly
      expect(tsValues).toEqual(expectedValues);
      expect(tsValues).toHaveLength(4);
    });

    it('should validate status transitions correctly', () => {
      // DRAFT can only transition to REVIEWING
      expect(
        EnumValidator.canTransitionStatus(
          TemplateStatus.DRAFT,
          TemplateStatus.REVIEWING
        )
      ).toBe(true);

      // DRAFT cannot transition to other statuses
      expect(
        EnumValidator.canTransitionStatus(
          TemplateStatus.DRAFT,
          TemplateStatus.PUBLISHED
        )
      ).toBe(false);
      expect(
        EnumValidator.canTransitionStatus(
          TemplateStatus.DRAFT,
          TemplateStatus.ARCHIVED
        )
      ).toBe(false);
    });
  });

  describe('Type Safety', () => {
    it('should work with template and field interfaces', () => {
      // Test that our interfaces work with the enums
      const field = {
        id: 1,
        name: 'test_field',
        label: 'Test Field',
        type: FieldType.EMAIL,
        required: true,
        order: 1,
      };

      const template = {
        id: 1,
        name: 'Test Template',
        status: TemplateStatus.DRAFT,
        fields: [field],
      };

      expect(field.type).toBe(FieldType.EMAIL);
      expect(template.status).toBe(TemplateStatus.DRAFT);
      expect(template.fields).toHaveLength(1);
    });
  });
});
