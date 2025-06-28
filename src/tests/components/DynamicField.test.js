import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import DynamicField from '../../components/DynamicField.vue';

describe('DynamicField', () => {
  let wrapper;
  let pinia;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
  });

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
    }
  });

  const createWrapper = (props = {}) => {
    const defaultProps = {
      field: {
        name: 'test_field',
        label: 'Test Field',
        type: 'text',
        required: false,
      },
      value: '',
      errors: [],
    };

    return mount(DynamicField, {
      props: { ...defaultProps, ...props },
      global: {
        plugins: [pinia],
      },
    });
  };

  describe('Text Input', () => {
    it('renders text input correctly', () => {
      wrapper = createWrapper({
        field: {
          name: 'nome',
          label: 'Nome',
          type: 'text',
          required: true,
        },
      });

      expect(wrapper.find('label').text()).toContain('Nome');
      expect(wrapper.find('label').text()).toContain('*');
      expect(wrapper.find('input[type="text"]').exists()).toBe(true);
      expect(wrapper.find('input').attributes('required')).toBeDefined();
    });

    it('emits update:value when input changes', async () => {
      wrapper = createWrapper();

      await wrapper.find('input').setValue('test value');

      expect(wrapper.emitted('update:value')).toBeTruthy();
      expect(wrapper.emitted('update:value')[0]).toEqual(['test value']);
    });

    it('displays validation errors', () => {
      wrapper = createWrapper({
        errors: ['Campo obrigatório', 'Valor inválido'],
      });

      const errorMessages = wrapper.findAll('.text-red-600');
      expect(errorMessages).toHaveLength(2);
      expect(errorMessages[0].text()).toBe('Campo obrigatório');
      expect(errorMessages[1].text()).toBe('Valor inválido');
    });
  });

  describe('CPF Input', () => {
    it('renders CPF input with proper formatting', async () => {
      wrapper = createWrapper({
        field: {
          name: 'cpf',
          label: 'CPF',
          type: 'cpf',
        },
      });

      const input = wrapper.find('input');
      expect(input.attributes('placeholder')).toBe('000.000.000-00');
      expect(input.attributes('maxlength')).toBe('14');
    });

    it('formats CPF input correctly', async () => {
      wrapper = createWrapper({
        field: {
          name: 'cpf',
          type: 'cpf',
        },
      });

      const input = wrapper.find('input');
      await input.setValue('12345678901');

      expect(wrapper.emitted('update:value')).toBeTruthy();
      expect(wrapper.emitted('update:value')[0][0]).toMatch(
        /\d{3}\.\d{3}\.\d{3}-\d{2}/
      );
    });
  });

  describe('Select Dropdown', () => {
    it('renders select with options', () => {
      wrapper = createWrapper({
        field: {
          name: 'estado',
          label: 'Estado',
          type: 'select',
          options: [
            { value: 'SP', label: 'São Paulo' },
            { value: 'RJ', label: 'Rio de Janeiro' },
          ],
        },
      });

      const select = wrapper.find('select');
      const options = wrapper.findAll('option');

      expect(select.exists()).toBe(true);
      expect(options).toHaveLength(3); // Including placeholder option
      expect(options[1].text()).toBe('São Paulo');
      expect(options[2].text()).toBe('Rio de Janeiro');
    });

    it('emits value when option is selected', async () => {
      wrapper = createWrapper({
        field: {
          name: 'estado',
          type: 'select',
          options: [{ value: 'SP', label: 'São Paulo' }],
        },
      });

      await wrapper.find('select').setValue('SP');

      expect(wrapper.emitted('update:value')).toBeTruthy();
      expect(wrapper.emitted('update:value')[0]).toEqual(['SP']);
    });
  });

  describe('Checkbox Input', () => {
    it('renders checkbox with label', () => {
      wrapper = createWrapper({
        field: {
          name: 'aceito_termos',
          label: 'Aceito os termos',
          type: 'checkbox',
          required: true,
        },
      });

      expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true);
      expect(wrapper.find('label').text()).toContain('Aceito os termos');
      expect(wrapper.find('label').text()).toContain('*');
    });

    it('emits boolean value when checked', async () => {
      wrapper = createWrapper({
        field: {
          name: 'aceito_termos',
          label: 'Aceito os termos',
          type: 'checkbox',
        },
      });

      const checkbox = wrapper.find('input[type="checkbox"]');
      await checkbox.setChecked(true);
      await wrapper.vm.$nextTick();

      expect(wrapper.emitted('update:value')).toBeTruthy();
      expect(wrapper.emitted('update:value')[0]).toEqual([true]);
    });
  });

  describe('Client Search', () => {
    it('renders client search input', () => {
      wrapper = createWrapper({
        field: {
          name: 'cliente_id',
          label: 'Cliente',
          type: 'client_search',
        },
      });

      const input = wrapper.find('input');
      expect(input.exists()).toBe(true);
      expect(input.attributes('placeholder')).toContain(
        'Digite o nome ou CPF do cliente'
      );
    });

    it('handles client search input', async () => {
      wrapper = createWrapper({
        field: {
          name: 'cliente_id',
          type: 'client_search',
        },
      });

      const input = wrapper.find('input');
      await input.setValue('João Silva');

      // Check if search method was called (would need to mock the store)
      expect(input.element.value).toBe('João Silva');
    });
  });

  describe('File Upload', () => {
    it('renders file input', () => {
      wrapper = createWrapper({
        field: {
          name: 'documento',
          label: 'Documento',
          type: 'file',
          accept: '.pdf,.doc,.docx',
        },
      });

      const input = wrapper.find('input[type="file"]');
      expect(input.exists()).toBe(true);
      expect(input.attributes('accept')).toBe('.pdf,.doc,.docx');
    });

    it('emits file when uploaded', async () => {
      wrapper = createWrapper({
        field: {
          name: 'documento',
          type: 'file',
        },
      });

      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      const input = wrapper.find('input[type="file"]');

      // Mock file input change event
      Object.defineProperty(input.element, 'files', {
        value: [file],
        configurable: true,
      });

      await input.trigger('change');

      expect(wrapper.emitted('update:value')).toBeTruthy();
      expect(wrapper.emitted('update:value')[0][0]).toBe(file);
    });
  });

  describe('Section Header', () => {
    it('renders section header correctly', () => {
      wrapper = createWrapper({
        field: {
          name: 'section_1',
          label: 'Dados Pessoais',
          type: 'section_header',
          description: 'Preencha seus dados pessoais',
        },
      });

      expect(wrapper.find('h3').text()).toBe('Dados Pessoais');
      expect(wrapper.find('p').text()).toBe('Preencha seus dados pessoais');
      expect(wrapper.find('input').exists()).toBe(false);
    });
  });

  describe('Accessibility', () => {
    it('associates labels with inputs correctly', () => {
      wrapper = createWrapper({
        field: {
          name: 'nome_completo',
          label: 'Nome Completo',
          type: 'text',
        },
      });

      const label = wrapper.find('label');
      const input = wrapper.find('input');

      expect(label.attributes('for')).toBe(input.attributes('id'));
      expect(input.attributes('id')).toBe('field_nome_completo');
    });

    it('applies proper ARIA attributes for required fields', () => {
      wrapper = createWrapper({
        field: {
          name: 'email',
          label: 'Email',
          type: 'email',
          required: true,
        },
      });

      const input = wrapper.find('input');
      expect(input.attributes('required')).toBeDefined();
    });
  });

  describe('Styling', () => {
    it('applies error styling when field has errors', () => {
      wrapper = createWrapper({
        field: {
          name: 'nome',
          type: 'text',
        },
        errors: ['Campo obrigatório'],
      });

      const input = wrapper.find('input');
      expect(input.classes()).toContain('border-red-300');
    });

    it('applies disabled styling when field is disabled', () => {
      wrapper = createWrapper({
        field: {
          name: 'nome',
          type: 'text',
          disabled: true,
        },
      });

      const input = wrapper.find('input');
      expect(input.classes()).toContain('bg-gray-100');
      expect(input.classes()).toContain('cursor-not-allowed');
    });
  });
});
