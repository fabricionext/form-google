// services/errorHandler.js
class ErrorHandler {
  static instance = null;
  
  constructor() {
    if (ErrorHandler.instance) {
      return ErrorHandler.instance;
    }
    
    this.errorQueue = [];
    this.maxQueueSize = 100;
    this.isOnline = navigator.onLine;
    
    // Listen for network status changes
    window.addEventListener('online', () => { this.isOnline = true; });
    window.addEventListener('offline', () => { this.isOnline = false; });
    
    ErrorHandler.instance = this;
  }
  
  static getInstance() {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }
  
  handleError(error, context, severity = 'medium') {
    const errorEntry = {
      error,
      context,
      severity,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      isOnline: this.isOnline
    };
    
    // Log estruturado
    this.logError(errorEntry);
    
    // Notificar usuário baseado na severidade
    this.notifyUser(errorEntry);
    
    // Queue para telemetria quando voltar online
    this.queueTelemetry(errorEntry);
    
    // Retry automático se aplicável
    if (this.isRetriable(error)) {
      return this.scheduleRetry(error, context);
    }
    
    return Promise.reject(error);
  }
  
  logError({ error, context, severity, timestamp }) {
    const logMethod = this.getLogMethod(severity);
    const errorInfo = {
      message: error.message,
      stack: error.stack,
      name: error.name,
      context,
      severity,
      timestamp
    };
    
    logMethod(`[${severity.toUpperCase()}] ${context}:`, errorInfo);
  }
  
  getLogMethod(severity) {
    switch (severity) {
      case 'critical': return console.error;
      case 'high': return console.error;
      case 'medium': return console.warn;
      case 'low': return console.info;
      default: return console.log;
    }
  }
  
  notifyUser({ error, severity, context }) {
    // Evitar spam de notificações
    if (this.isSpamming(error, context)) {
      return;
    }
    
    const notification = this.createNotification(error, severity, context);
    
    if (window.app && window.app.$toast) {
      window.app.$toast[notification.type](notification.message, {
        icon: notification.icon,
        timeout: notification.timeout
      });
    }
  }
  
  createNotification(error, severity, context) {
    const notifications = {
      critical: {
        type: 'error',
        message: 'Erro crítico no sistema. Tente recarregar a página.',
        icon: 'mdi-alert-circle',
        timeout: 0 // Não remove automaticamente
      },
      high: {
        type: 'error',
        message: 'Erro no sistema. Algumas funcionalidades podem estar indisponíveis.',
        icon: 'mdi-alert',
        timeout: 8000
      },
      medium: {
        type: 'warning',
        message: 'Operação falhou. Tentando novamente...',
        icon: 'mdi-alert-outline',
        timeout: 5000
      },
      low: {
        type: 'info',
        message: 'Informação salva localmente. Será sincronizada quando possível.',
        icon: 'mdi-information',
        timeout: 3000
      }
    };
    
    return notifications[severity] || notifications.medium;
  }
  
  isSpamming(error, context) {
    const key = `${error.name}:${context}`;
    const now = Date.now();
    const threshold = 5000; // 5 segundos
    
    if (!this.lastNotification) {
      this.lastNotification = new Map();
    }
    
    const lastTime = this.lastNotification.get(key);
    if (lastTime && (now - lastTime) < threshold) {
      return true;
    }
    
    this.lastNotification.set(key, now);
    return false;
  }
  
  isRetriable(error) {
    // Condições para retry automático
    return (
      error.name === 'NetworkError' ||
      error.message.includes('timeout') ||
      error.message.includes('network') ||
      (error.response && error.response.status >= 500) ||
      (error.response && error.response.status === 429) // Rate limit
    );
  }
  
  scheduleRetry(error, context, attempt = 1, maxAttempts = 3) {
    if (attempt > maxAttempts) {
      return Promise.reject(new Error(`Max retry attempts exceeded: ${error.message}`));
    }
    
    const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000); // Exponential backoff, max 10s
    
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        console.info(`Retry attempt ${attempt}/${maxAttempts} for: ${context}`);
        resolve(); // A função que chama precisa implementar o retry
      }, delay);
    });
  }
  
  queueTelemetry(errorEntry) {
    if (this.errorQueue.length >= this.maxQueueSize) {
      this.errorQueue.shift(); // Remove o mais antigo
    }
    
    this.errorQueue.push(errorEntry);
    
    // Tentar enviar se estiver online
    if (this.isOnline) {
      this.flushTelemetry();
    }
  }
  
  async flushTelemetry() {
    if (this.errorQueue.length === 0) {
      return;
    }
    
    try {
      // Implementar envio de telemetria quando tiver endpoint
      // await this.sendTelemetryBatch(this.errorQueue);
      console.info(`Telemetry queue flushed: ${this.errorQueue.length} errors`);
      this.errorQueue.length = 0;
    } catch (error) {
      console.warn('Failed to send telemetry:', error);
    }
  }
  
  // Method para componentes reportarem erros
  reportError(error, component, action, severity = 'medium') {
    const context = `${component}:${action}`;
    return this.handleError(error, context, severity);
  }
  
  // Cleanup method
  destroy() {
    this.flushTelemetry();
    this.errorQueue.length = 0;
    this.lastNotification?.clear();
    window.removeEventListener('online', this.onlineHandler);
    window.removeEventListener('offline', this.offlineHandler);
  }
}

export default ErrorHandler;