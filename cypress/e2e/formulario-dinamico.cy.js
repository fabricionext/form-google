/**
 * TESTE E2E CRÍTICO - FORMULÁRIO DINÂMICO (QDD/TDD Fase 5)
 */

describe('Formulário Dinâmico - Fluxo Principal', () => {
  beforeEach(() => {
    cy.visit('/peticionador/formularios/dinamico')
    cy.injectAxe()
  })
  
  it('should have no accessibility violations', () => {
    cy.get('[data-cy="formulario-dinamico"]').should('be.visible')
    cy.checkA11y()
  })
  
  it('should complete form submission workflow', () => {
    // Selecionar template
    cy.get('[data-cy="template-select"]').select('suspensao-condicional')
    
    // Preencher dados
    cy.fillClientForm({
      nome: 'João Silva Santos',
      cpf: '123.456.789-09',
      email: 'joao.silva@example.com'
    })
    
    // Submeter
    cy.get('[data-cy="submit-button"]').click()
    
    // Verificar sucesso
    cy.get('[data-cy="success-message"]', { timeout: 30000 }).should('be.visible')
  })
  
  it('should validate fields in real-time', () => {
    cy.get('[data-cy="template-select"]').select('suspensao-condicional')
    cy.get('[data-cy="submit-button"]').click()
    
    // Verificar erros
    cy.get('[data-cy="error-nome"]').should('be.visible')
    cy.get('[data-cy="submit-button"]').should('be.disabled')
    
    // Corrigir e verificar
    cy.get('[data-cy="nome-input"]').type('João Silva')
    cy.get('[data-cy="error-nome"]').should('not.exist')
  })
})

Cypress.Commands.add('tab', { prevSubject: 'optional' }, (subject) => {
  return cy.wrap(subject).trigger('keydown', { key: 'Tab' })
})
