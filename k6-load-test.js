/**
 * TESTE DE CARGA K6 - QDD/TDD FASE 5
 * ==================================
 * 
 * Meta: APIs críticas devem responder em <300ms sob carga normal
 */

import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate } from 'k6/metrics'

// Métricas customizadas
export const errorRate = new Rate('errors')

// Configuração de carga
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up
    { duration: '1m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<300'], // 95% das requests <300ms
    http_req_failed: ['rate<0.05'],   // <5% de falhas
    errors: ['rate<0.1'],             // <10% de erros de negócio
  },
}

const BASE_URL = 'http://localhost:5000'

export default function () {
  // 1. Teste de health check
  let response = http.get(`${BASE_URL}/health`)
  check(response, {
    'health check status is 200': (r) => r.status === 200,
  })
  
  // 2. Teste das APIs críticas
  
  // API Templates
  response = http.get(`${BASE_URL}/api/templates/`)
  check(response, {
    'templates API status is 200': (r) => r.status === 200,
    'templates response time < 300ms': (r) => r.timings.duration < 300,
  }) || errorRate.add(1)
  
  // API Forms Schema
  response = http.get(`${BASE_URL}/api/forms/schema/suspensao-condicional`)
  check(response, {
    'form schema status is 200': (r) => r.status === 200,
    'form schema has fields': (r) => r.json().fields !== undefined,
  }) || errorRate.add(1)
  
  // API Clients Search (simulando busca)
  response = http.get(`${BASE_URL}/api/clients/?search=João`)
  check(response, {
    'client search status is 200': (r) => r.status === 200,
    'client search response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1)
  
  // Simular geração de documento (POST)
  const payload = JSON.stringify({
    template_slug: 'suspensao-condicional',
    cliente_data: {
      nome: 'Cliente Teste K6',
      cpf: '123.456.789-09'
    },
    form_data: {
      data_suspensao: '2024-12-31',
      periodo_prova: '2'
    }
  })
  
  response = http.post(`${BASE_URL}/api/documents/generate`, payload, {
    headers: { 'Content-Type': 'application/json' },
  })
  
  check(response, {
    'document generation accepted': (r) => r.status === 202,
    'document generation has task_id': (r) => r.json().task_id !== undefined,
  }) || errorRate.add(1)
  
  sleep(1) // Pausa entre iterações
}

export function handleSummary(data) {
  return {
    'performance-report.json': JSON.stringify(data, null, 2),
    'performance-report.html': `
      <html>
        <head><title>K6 Performance Report</title></head>
        <body>
          <h1>Performance Test Results</h1>
          <h2>Summary</h2>
          <p>VUs: ${data.metrics.vus.max}</p>
          <p>Duration: ${data.state.testRunDurationMs}ms</p>
          <p>Requests: ${data.metrics.http_reqs.count}</p>
          <p>Failed Requests: ${data.metrics.http_req_failed.rate * 100}%</p>
          <p>Avg Response Time: ${data.metrics.http_req_duration.avg}ms</p>
          <p>95th Percentile: ${data.metrics['http_req_duration{p(95)}']}ms</p>
        </body>
      </html>
    `,
  }
}
