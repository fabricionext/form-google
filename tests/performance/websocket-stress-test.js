/**
 * K6 WebSocket Stress Testing - Fase 3
 * ====================================
 * 
 * Testes de stress para WebSocket real-time monitoring:
 * - Múltiplas conexões simultâneas
 * - Latência < 500ms
 * - Reconexão automática
 * - Memory efficiency
 */

import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
export let wsConnectionRate = new Rate('websocket_connection_success_rate');
export let wsLatency = new Trend('websocket_message_latency');
export let wsReconnections = new Counter('websocket_reconnections');
export let concurrentConnections = new Counter('concurrent_websocket_connections');

export let options = {
  stages: [
    { duration: '1m', target: 10 },   // 10 WebSocket connections
    { duration: '2m', target: 50 },   // 50 concurrent connections
    { duration: '1m', target: 100 },  // Peak: 100 connections
    { duration: '3m', target: 100 },  // Sustain peak load
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'websocket_connection_success_rate': ['rate>0.95'],
    'websocket_message_latency': ['p(95)<500'], // < 500ms latency
  },
};

const WS_URL = __ENV.WS_URL || 'ws://localhost:5000/ws/monitoring';

export default function () {
  const taskId = `stress-task-${__VU}-${__ITER}`;
  
  const url = `${WS_URL}?task_id=${taskId}`;
  
  const res = ws.connect(url, {}, function (socket) {
    concurrentConnections.add(1);
    
    let connectionSuccess = true;
    let messageCount = 0;
    const maxMessages = 20;
    
    socket.on('open', function open() {
      console.log(`✅ WebSocket connected for task ${taskId}`);
      wsConnectionRate.add(true);
      
      // Subscribe to task updates
      const subscribeMessage = JSON.stringify({
        type: 'subscribe',
        task_id: taskId
      });
      
      socket.send(subscribeMessage);
    });

    socket.on('message', function (message) {
      const receiveTime = Date.now();
      messageCount++;
      
      try {
        const data = JSON.parse(message);
        
        // Calculate latency if timestamp is provided
        if (data.timestamp) {
          const latency = receiveTime - data.timestamp;
          wsLatency.add(latency);
          
          // Check latency requirement
          check(latency, {
            'WebSocket latency < 500ms': (l) => l < 500,
          });
        }
        
        // Validate message structure
        check(data, {
          'Message has task_id': (d) => d.task_id !== undefined,
          'Message has type': (d) => d.type !== undefined,
        });
        
        // Simulate progress updates
        if (data.type === 'progress_update') {
          console.log(`📊 Task ${taskId} progress: ${data.progress}%`);
          
          // Send acknowledgment
          const ackMessage = JSON.stringify({
            type: 'ack',
            message_id: data.message_id || messageCount
          });
          
          socket.send(ackMessage);
        }
        
      } catch (e) {
        console.error(`❌ Failed to parse WebSocket message: ${e}`);
        connectionSuccess = false;
      }
      
      // Close connection after receiving enough messages
      if (messageCount >= maxMessages) {
        socket.close();
      }
    });

    socket.on('close', function close() {
      console.log(`🔌 WebSocket closed for task ${taskId}`);
      concurrentConnections.add(-1);
      
      // Check if we should attempt reconnection
      if (messageCount < maxMessages && connectionSuccess) {
        console.log(`🔄 Attempting reconnection for task ${taskId}`);
        wsReconnections.add(1);
        
        // Simulate reconnection attempt after short delay
        sleep(1);
      }
    });

    socket.on('error', function (e) {
      console.error(`❌ WebSocket error for task ${taskId}: ${e.error()}`);
      wsConnectionRate.add(false);
      connectionSuccess = false;
    });

    // Simulate real-time interaction
    socket.setTimeout(function () {
      // Send periodic heartbeat
      const heartbeat = JSON.stringify({
        type: 'heartbeat',
        task_id: taskId,
        timestamp: Date.now()
      });
      
      socket.send(heartbeat);
    }, 5000);

    // Keep connection alive for test duration
    socket.setTimeout(function () {
      socket.close();
    }, 30000); // Close after 30 seconds
  });

  check(res, {
    'WebSocket connection established': (r) => r && r.url !== '',
  });

  if (!res) {
    wsConnectionRate.add(false);
    console.error(`❌ Failed to establish WebSocket connection for task ${taskId}`);
  }

  // Sleep between iterations
  sleep(1 + Math.random() * 2);
}

export function teardown() {
  console.log('🏁 WebSocket Stress Test Completed');
  console.log('Metrics to validate:');
  console.log('- Connection Success Rate: > 95%');
  console.log('- Message Latency: p95 < 500ms');
  console.log('- Reconnection Handling: Functional');
}
