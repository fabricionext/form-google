/**
 * Template Manager - E2E Integration Tests (Fase 2 TDD/QDD)
 * Testa integração completa Vue.js + TypeScript + ENUMs Python
 */

describe('Template Manager - Integração Completa TDD Fase 2', () => {
  beforeEach(() => {
    // Mock das APIs backend
    cy.intercept('GET', '/api/templates/', { fixture: 'templates.json' }).as('getTemplates')
    cy.intercept('GET', '/api/field-types/', { fixture: 'field-types.json' }).as('getFieldTypes')
    cy.intercept('POST', '/api/templates/', { fixture: 'template-created.json' }).as('createTemplate')
  })

  describe('ENUM Integration E2E', () => {
    it('should validate ENUM consistency between frontend and backend', () => {
      // Given: Template Manager page
      cy.visit('/admin/templates/new')
      
      // When: Check field types match ENUMs
      cy.wait('@getFieldTypes')
      
      // Then: Should have consistent ENUM values
      cy.get('[data-cy="field-type-select"]').should('exist')
      
      // Verify key ENUM values exist
      cy.get('[data-cy="field-type-option-text"]').should('contain', 'text')
      cy.get('[data-cy="field-type-option-email"]').should('contain', 'email')
      cy.get('[data-cy="field-type-option-number"]').should('contain', 'number')
    })

    it('should create template with ENUM validation', () => {
      // Given: New template form
      cy.visit('/admin/templates/new')
      
      // When: Fill form with valid ENUM values
      cy.get('[data-cy="template-name"]').type('Template E2E Test')
      cy.get('[data-cy="template-status"]').select('draft')
      
      // Add field with valid ENUM type
      cy.get('[data-cy="add-field-button"]').click()
      cy.get('[data-cy="field-name-0"]').type('nome_cliente')
      cy.get('[data-cy="field-type-0"]').select('text')
      
      // When: Submit form
      cy.get('[data-cy="save-template-button"]').click()
      
      // Then: Should create successfully
      cy.wait('@createTemplate')
      cy.get('[data-cy="success-message"]').should('be.visible')
    })
  })

  describe('Performance Tests', () => {
    it('should load under 2 seconds', () => {
      const startTime = Date.now()
      
      cy.visit('/admin/templates').then(() => {
        const loadTime = Date.now() - startTime
        expect(loadTime).to.be.lessThan(2000)
      })
    })
  })
})
