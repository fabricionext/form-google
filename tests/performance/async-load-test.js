/**
 * K6 Load Testing - Processamento Assíncrono - Fase 3
 * ====================================================
 * 
 * Testes de carga para validar performance do sistema:
 * - > 100 documentos/minuto
 * - < 30s completion time
 * - < 200ms API response time
 * - Estabilidade sob carga
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
export let documentGenerationRate = new Rate('document_generation_success_rate');
export let documentGenerationDuration = new Trend('document_generation_duration');
export let apiResponseTime = new Trend('api_response_time');
export let concurrentTasks = new Counter('concurrent_tasks_count');

// Test configuration
export let options = {
  stages: [
    // Ramp up
    { duration: '2m', target: 20 }, // 20 concurrent users
    { duration: '5m', target: 50 }, // 50 concurrent users
    { duration: '2m', target: 100 }, // Peak: 100 concurrent users
    { duration: '5m', target: 100 }, // Stay at peak
    { duration: '2m', target: 0 },   // Ramp down
  ],
  thresholds: {
    // Performance requirements from Fase 3
    'http_req_duration': ['p(95)<200'], // 95% of requests under 200ms
    'document_generation_success_rate': ['rate>0.95'], // 95% success rate
    'document_generation_duration': ['p(95)<30000'], // 95% under 30s
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';

export function setup() {
  // Setup test data
  console.log('🚀 Starting Async Load Test - Fase 3');
  console.log('Target: >100 docs/minute, <30s completion, <200ms API response');
  
  return {
    templates: ['suspensao-condicional', 'acao-anulatoria', 'embargo-declaracao'],
    testUsers: generateTestUsers(1000)
  };
}

export default function(data) {
  const testUser = data.testUsers[Math.floor(Math.random() * data.testUsers.length)];
  const template = data.templates[Math.floor(Math.random() * data.templates.length)];
  
  // Phase 1: Submit async document generation
  const startTime = Date.now();
  
  const payload = {
    template_id: template,
    form_data: {
      nome: testUser.nome,
      cpf: testUser.cpf,
      email: testUser.email,
      rg: testUser.rg
    }
  };

  const headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'K6-LoadTest-Fase3'
  };

  // Submit generation request
  const submitResponse = http.post(`${BASE_URL}/api/gerar-documento`, 
    JSON.stringify(payload), 
    { headers }
  );

  const submitSuccess = check(submitResponse, {
    'Submit Status 202': (r) => r.status === 202,
    'Task ID returned': (r) => JSON.parse(r.body).task_id !== undefined,
    'Submit Response < 200ms': (r) => r.timings.duration < 200,
  });

  apiResponseTime.add(submitResponse.timings.duration);

  if (!submitSuccess) {
    console.error(`Submit failed: ${submitResponse.status} - ${submitResponse.body}`);
    return;
  }

  const taskId = JSON.parse(submitResponse.body).task_id;
  concurrentTasks.add(1);

  // Phase 2: Poll task status until completion
  let taskCompleted = false;
  let pollCount = 0;
  const maxPolls = 150; // 30s / 200ms = 150 polls
  
  while (!taskCompleted && pollCount < maxPolls) {
    sleep(0.2); // 200ms polling interval
    pollCount++;

    const statusResponse = http.get(`${BASE_URL}/api/task-status/${taskId}`, { headers });
    
    const statusCheck = check(statusResponse, {
      'Status API Response < 200ms': (r) => r.timings.duration < 200,
      'Status API Success': (r) => r.status === 200,
    });

    apiResponseTime.add(statusResponse.timings.duration);

    if (statusCheck && statusResponse.status === 200) {
      const statusData = JSON.parse(statusResponse.body);
      
      if (statusData.status === 'SUCCESS') {
        const totalDuration = Date.now() - startTime;
        documentGenerationDuration.add(totalDuration);
        documentGenerationRate.add(true);
        taskCompleted = true;
        
        // Validate completion requirements
        check(totalDuration, {
          'Document Generation < 30s': (duration) => duration < 30000,
        });
        
        console.log(`✅ Task ${taskId} completed in ${totalDuration}ms`);
        
      } else if (statusData.status === 'FAILURE') {
        documentGenerationRate.add(false);
        taskCompleted = true;
        console.error(`❌ Task ${taskId} failed: ${statusData.error_message}`);
        
      } else if (statusData.status === 'PROCESSING') {
        // Continue polling
        console.log(`🔄 Task ${taskId} progress: ${statusData.progress}%`);
      }
    } else {
      console.error(`Status check failed for ${taskId}: ${statusResponse.status}`);
    }
  }

  if (!taskCompleted) {
    // Timeout
    documentGenerationRate.add(false);
    console.error(`⏰ Task ${taskId} timed out after ${maxPolls * 200}ms`);
  }

  // Random sleep between requests (1-3 seconds)
  sleep(Math.random() * 2 + 1);
}

export function teardown(data) {
  console.log('🏁 Load Test Completed - Fase 3');
  console.log('Check results for compliance with performance requirements:');
  console.log('- API Response Time: p95 < 200ms');
  console.log('- Success Rate: > 95%');
  console.log('- Document Generation: p95 < 30s');
}

function generateTestUsers(count) {
  const users = [];
  const nomes = ['João Silva', 'Maria Santos', 'Pedro Costa', 'Ana Oliveira', 'Carlos Lima'];
  const sobrenomes = ['Santos', 'Silva', 'Costa', 'Oliveira', 'Lima', 'Souza', 'Pereira'];
  
  for (let i = 0; i < count; i++) {
    const nome = nomes[Math.floor(Math.random() * nomes.length)];
    const sobrenome = sobrenomes[Math.floor(Math.random() * sobrenomes.length)];
    
    users.push({
      nome: `${nome} ${sobrenome} ${i}`,
      cpf: generateCPF(),
      email: `user${i}@loadtest.com`,
      rg: `${Math.floor(Math.random() * 99999999) + 10000000}`
    });
  }
  
  return users;
}

function generateCPF() {
  // Generate a simple test CPF
  const n = Math.floor(Math.random() * 999999999) + 100000000;
  return n.toString().replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}
