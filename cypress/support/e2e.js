// Cypress E2E Support File
import 'cypress-axe'

// Comandos customizados para testes de acessibilidade
Cypress.Commands.add('checkA11y', (context, options) => {
  cy.injectAxe()
  cy.checkA11y(context, options)
})

// Comando para login (se necessário)
Cypress.Commands.add('login', (email = 'teste@example.com', password = 'senha123') => {
  cy.visit('/login')
  cy.get('[data-cy="email"]').type(email)
  cy.get('[data-cy="password"]').type(password)
  cy.get('[data-cy="login-button"]').click()
})

// Comando para preencher formulário de cliente
Cypress.Commands.add('fillClientForm', (clientData) => {
  if (clientData.nome) cy.get('[data-cy="nome"]').type(clientData.nome)
  if (clientData.cpf) cy.get('[data-cy="cpf"]').type(clientData.cpf)
  if (clientData.email) cy.get('[data-cy="email"]').type(clientData.email)
})
