/**
 * Testes E2E - Processamento Assíncrono - Fase 3 TDD/QDD
 * ========================================================
 * 
 * Testes críticos E2E para validar processamento assíncrono completo:
 * - Geração de documentos < 30s
 * - WebSocket real-time monitoring
 * - Handling de falhas e retry logic
 * - Performance sob carga
 */

describe('Processamento Assíncrono E2E - Fase 3', () => {
  beforeEach(() => {
    // Setup inicial
    cy.visit('/peticionador/formularios/dinamico');
    
    // Interceptar APIs para controle dos testes
    cy.intercept('GET', '/api/templates/', { fixture: 'templates.json' }).as('getTemplates');
    cy.intercept('POST', '/api/gerar-documento', {
      statusCode: 202,
      body: { 
        status: 'sucesso_enfileirado',
        task_id: 'test-task-123',
        message: 'Documento enfileirado para geração'
      }
    }).as('startAsyncGeneration');
    
    // Mock WebSocket connection
    cy.window().then((win) => {
      win.mockWebSocket = {
        connected: true,
        send: cy.stub().as('websocketSend'),
        addEventListener: cy.stub().as('websocketListener'),
        close: cy.stub().as('websocketClose')
      };
    });
  });

  describe('🚀 Geração Assíncrona Completa', () => {
    it('should complete async document generation end-to-end under 30s', () => {
      const startTime = Date.now();
      
      // Given: Formulário preenchido
      cy.get('[data-cy="template-select"]').select('suspensao-condicional');
      cy.get('[data-cy="nome-input"]').type('João Silva Santos');
      cy.get('[data-cy="cpf-input"]').type('123.456.789-09');
      cy.get('[data-cy="email-input"]').type('joao.silva@example.com');

      // When: Submit for async processing
      cy.get('[data-cy="generate-async-button"]').click();

      // Then: Should show task started immediately
      cy.wait('@startAsyncGeneration');
      cy.get('[data-cy="task-id"]').should('be.visible');
      cy.get('[data-cy="progress-bar"]').should('be.visible');
      cy.get('[data-cy="progress-percentage"]').should('contain', '0%');

      // Mock task progress updates via API
      cy.intercept('GET', '/api/task-status/test-task-123', {
        statusCode: 200,
        body: {
          task_id: 'test-task-123',
          status: 'PROCESSING',
          progress: 10,
          message: 'Iniciando geração...'
        }
      }).as('taskProgress10');

      // And: Should show real-time progress updates
      cy.get('[data-cy="progress-percentage"]', { timeout: 5000 })
        .should('contain', '10%');
      
      cy.get('[data-cy="progress-status"]')
        .should('contain', 'Iniciando geração');

      // Progress to 50%
      cy.intercept('GET', '/api/task-status/test-task-123', {
        statusCode: 200,
        body: {
          task_id: 'test-task-123',
          status: 'PROCESSING',
          progress: 50,
          message: 'Processando template...'
        }
      }).as('taskProgress50');

      cy.get('[data-cy="progress-percentage"]', { timeout: 10000 })
        .should('contain', '50%');

      // Final completion
      cy.intercept('GET', '/api/task-status/test-task-123', {
        statusCode: 200,
        body: {
          task_id: 'test-task-123',
          status: 'SUCCESS',
          progress: 100,
          message: 'Documento gerado com sucesso',
          result: {
            document_url: '/downloads/documento-gerado-123.pdf',
            filename: 'suspensao_condicional_joao_silva.pdf'
          }
        }
      }).as('taskComplete');

      // And: Should complete successfully
      cy.get('[data-cy="progress-percentage"]', { timeout: 30000 })
        .should('contain', '100%');
      
      cy.get('[data-cy="completion-message"]')
        .should('be.visible')
        .and('contain', 'Documento gerado com sucesso');

      // And: Should provide download link
      cy.get('[data-cy="download-link"]')
        .should('be.visible')
        .and('have.attr', 'href');

      // Validate performance requirement
      cy.then(() => {
        const duration = Date.now() - startTime;
        expect(duration).to.be.lessThan(30000, 'Generation should complete under 30 seconds');
      });
    });

    it('should handle async task failures gracefully with retry mechanism', () => {
      // Given: Force a task failure scenario
      cy.intercept('POST', '/api/gerar-documento', {
        statusCode: 202,
        body: { 
          status: 'sucesso_enfileirado',
          task_id: 'failing-task-456'
        }
      }).as('startFailingTask');

      // Mock initial progress then failure
      cy.intercept('GET', '/api/task-status/failing-task-456', (req) => {
        // Return different responses based on call count
        req.reply({
          statusCode: 200,
          body: {
            task_id: 'failing-task-456',
            status: 'FAILURE',
            progress: 0,
            error_message: 'Google API timeout after 3 retries',
            retry_count: 3,
            can_retry: true
          }
        });
      }).as('taskFailure');

      // When: Submit form
      cy.get('[data-cy="template-select"]').select('suspensao-condicional');
      cy.get('[data-cy="nome-input"]').type('Test Failure User');
      cy.get('[data-cy="generate-async-button"]').click();

      // Then: Should show failure handling
      cy.wait('@startFailingTask');
      cy.wait('@taskFailure');
      
      cy.get('[data-cy="error-message"]', { timeout: 10000 })
        .should('be.visible')
        .and('contain', 'Erro no processamento');

      cy.get('[data-cy="retry-button"]')
        .should('be.visible')
        .and('not.be.disabled');

      cy.get('[data-cy="error-details"]')
        .should('contain', 'Google API timeout');

      // When: Click retry
      cy.intercept('POST', '/api/retry-task/failing-task-456', {
        statusCode: 202,
        body: {
          status: 'sucesso_reenfileirado',
          task_id: 'retry-task-789',
          message: 'Task reenfileirada com sucesso'
        }
      }).as('retryTask');

      cy.get('[data-cy="retry-button"]').click();

      // Then: Should start retry process
      cy.wait('@retryTask');
      cy.get('[data-cy="retry-message"]')
        .should('be.visible')
        .and('contain', 'Tentando novamente');
    });
  });

  describe('⚡ Performance & Escalabilidade', () => {
    it('should handle multiple concurrent generations efficiently', () => {
      // Given: Multiple forms simulation
      const tasks = ['task-1', 'task-2', 'task-3'];
      
      tasks.forEach((taskId, index) => {
        cy.intercept('POST', '/api/gerar-documento', {
          statusCode: 202,
          body: { 
            status: 'sucesso_enfileirado',
            task_id: taskId,
            queue_position: index + 1
          }
        }).as(`startTask${index}`);
      });

      // When: Submit multiple forms (simulate concurrent users)
      cy.get('[data-cy="template-select"]').select('suspensao-condicional');
      cy.get('[data-cy="nome-input"]').type('Concurrent User 1');
      cy.get('[data-cy="generate-async-button"]').click();

      // Then: Should handle concurrent processing
      cy.wait('@startTask0');
      cy.get('[data-cy="task-id"]').should('be.visible');
      cy.get('[data-cy="queue-position"]')
        .should('be.visible')
        .and('contain', /Position: [1-3]/);

      // And: Should show queue management
      cy.get('[data-cy="queue-info"]')
        .should('be.visible')
        .and('contain', 'tasks na fila');
    });

    it('should maintain responsive UI during heavy processing', () => {
      // Given: Heavy processing simulation
      cy.intercept('POST', '/api/gerar-documento', {
        statusCode: 202,
        body: { 
          status: 'sucesso_enfileirado',
          task_id: 'heavy-task-999'
        }
      }).as('startHeavyTask');

      // Slow progress updates
      cy.intercept('GET', '/api/task-status/heavy-task-999', {
        statusCode: 200,
        body: {
          task_id: 'heavy-task-999',
          status: 'PROCESSING',
          progress: 5,
          message: 'Processando documento complexo...',
          estimated_time: 25000
        }
      }).as('heavyTaskProgress');

      // When: Start heavy processing
      cy.get('[data-cy="template-select"]').select('suspensao-condicional');
      cy.get('[data-cy="nome-input"]').type('Heavy Processing User');
      cy.get('[data-cy="generate-async-button"]').click();

      // Then: UI should remain responsive
      cy.wait('@startHeavyTask');
      
      // Test UI responsiveness during processing
      cy.get('[data-cy="cancel-button"]').should('be.visible');
      cy.get('[data-cy="estimated-time"]').should('contain', '25 seconds');
      
      // Interact with other UI elements
      cy.get('[data-cy="template-select"]').should('not.be.disabled');
      cy.get('body').should('not.have.class', 'loading');
    });
  });

  describe('🔄 WebSocket Real-time Updates', () => {
    it('should receive real-time progress via WebSocket connection', () => {
      // Given: WebSocket connection mock
      cy.window().then((win) => {
        // Enhanced WebSocket mock
        win.WebSocket = class MockWebSocket {
          constructor(url) {
            this.url = url;
            this.readyState = 1; // OPEN
            this.onopen = null;
            this.onmessage = null;
            this.onerror = null;
            this.onclose = null;
            
            // Simulate connection established
            setTimeout(() => {
              if (this.onopen) this.onopen({ type: 'open' });
            }, 100);
          }
          
          send(data) {
            cy.log('WebSocket send:', data);
          }
          
          close() {
            this.readyState = 3; // CLOSED
            if (this.onclose) this.onclose({ type: 'close' });
          }
          
          // Simulate receiving progress updates
          simulateProgressUpdate(data) {
            if (this.onmessage) {
              this.onmessage({ 
                type: 'message', 
                data: JSON.stringify(data) 
              });
            }
          }
        };
      });

      // When: Start async generation
      cy.get('[data-cy="template-select"]').select('suspensao-condicional');
      cy.get('[data-cy="nome-input"]').type('WebSocket Test User');
      cy.get('[data-cy="generate-async-button"]').click();

      // Then: Should show WebSocket connection
      cy.get('[data-cy="websocket-status"]', { timeout: 5000 })
        .should('contain', 'Conectado');

      // And: Should show real-time indicator
      cy.get('[data-cy="real-time-indicator"]')
        .should('be.visible')
        .and('have.class', 'active');
    });
  });
});
