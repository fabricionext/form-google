import { describe, it, expect, vi } from 'vitest';
import GoogleDocsSync from '@/services/googleDocsSync';

describe('GoogleDocsSync', () => {
  it('should analyze document fields and return enhanced data', async () => {
    const apiClient = {
      post: vi.fn().mockResolvedValue({
        data: {
          content: 'Document content with {{field1}} and {{field2}}',
          detected_fields: [
            { name: 'field1', position: 23 },
            { name: 'field2', position: 45 },
          ],
          metadata: { title: 'Test Document' },
        },
      }),
    };

    const googleDocsSync = new GoogleDocsSync(apiClient);

    // Mock auxiliary methods to isolate the test
    googleDocsSync.performAdvancedFieldAnalysis = vi.fn().mockReturnValue({
      fields: [
        { name: 'field1', label: 'Field 1', type: 'text' },
        { name: 'field2', label: 'Field 2', type: 'text' },
      ],
      validation_rules: {},
      field_types: {},
      dependencies: [],
      complexity_score: 0.2,
      estimated_fill_time: 5,
    });

    const result = await googleDocsSync.analyzeDocumentFields('test_document_id');

    expect(apiClient.post).toHaveBeenCalledWith('/api/admin/google-docs/analyze', {
      document_id: 'test_document_id',
    });

    expect(googleDocsSync.performAdvancedFieldAnalysis).toHaveBeenCalled();

    expect(result).toEqual({
      content: 'Document content with {{field1}} and {{field2}}',
      fields: [
        { name: 'field1', label: 'Field 1', type: 'text' },
        { name: 'field2', label: 'Field 2', type: 'text' },
      ],
      validation_rules: {},
      field_types: {},
      dependencies: [],
      metadata: {
        title: 'Test Document',
        complexity_score: 0.2,
        estimated_fill_time: 5,
      },
    });
  });
});
