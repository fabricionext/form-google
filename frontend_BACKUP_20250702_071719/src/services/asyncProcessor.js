// services/asyncProcessor.js
/**
 * Async processor for handling large datasets without blocking the UI
 */
class AsyncProcessor {
  constructor(options = {}) {
    this.options = {
      batchSize: 5,
      yieldInterval: 16, // ~60fps
      timeout: 5000,
      maxConcurrency: 3,
      ...options
    };
  }
  
  /**
   * Process items in batches with yielding to prevent UI blocking
   */
  async processInBatches(items, processor, options = {}) {
    const config = { ...this.options, ...options };
    const results = [];
    let processed = 0;
    
    for (let i = 0; i < items.length; i += config.batchSize) {
      const batch = items.slice(i, i + config.batchSize);
      
      // Process batch with timeout protection
      const batchPromises = batch.map(item => 
        this.processWithTimeout(processor(item), config.timeout)
      );
      
      const batchResults = await Promise.allSettled(batchPromises);
      results.push(...batchResults);
      
      processed += batch.length;
      
      // Emit progress if callback provided
      if (config.onProgress) {
        config.onProgress({
          processed,
          total: items.length,
          percentage: Math.round((processed / items.length) * 100)
        });
      }
      
      // Yield control to prevent UI blocking
      if (i + config.batchSize < items.length) {
        await this.yield(config.yieldInterval);
      }
    }
    
    return results;
  }
  
  /**
   * Process with timeout protection
   */
  async processWithTimeout(promise, timeout) {
    return Promise.race([
      promise,
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error(`Timeout after ${timeout}ms`)), timeout)
      )
    ]);
  }
  
  /**
   * Yield control to the event loop
   */
  async yield(interval = 16) {
    return new Promise(resolve => setTimeout(resolve, interval));
  }
  
  /**
   * Process with controlled concurrency
   */
  async processWithConcurrency(items, processor, maxConcurrency = 3) {
    const results = [];
    const inProgress = new Set();
    
    for (const item of items) {
      // Wait if we're at max concurrency
      while (inProgress.size >= maxConcurrency) {
        await Promise.race(inProgress);
      }
      
      // Start processing
      const promise = processor(item)
        .then(result => {
          inProgress.delete(promise);
          return result;
        })
        .catch(error => {
          inProgress.delete(promise);
          throw error;
        });
      
      inProgress.add(promise);
      results.push(promise);
    }
    
    // Wait for all to complete
    return Promise.allSettled(results);
  }
  
  /**
   * Debounced processing (useful for user input)
   */
  createDebouncedProcessor(processor, delay = 300) {
    let timeoutId;
    let latestResolve;
    let latestReject;
    
    return (input) => {
      return new Promise((resolve, reject) => {
        latestResolve = resolve;
        latestReject = reject;
        
        clearTimeout(timeoutId);
        timeoutId = setTimeout(async () => {
          try {
            const result = await processor(input);
            latestResolve(result);
          } catch (error) {
            latestReject(error);
          }
        }, delay);
      });
    };
  }
  
  /**
   * Queue processor with priority support
   */
  createQueueProcessor() {
    const queue = [];
    let isProcessing = false;
    
    const enqueue = (task, priority = 'normal') => {
      const queueItem = {
        id: Date.now() + Math.random(),
        task,
        priority,
        promise: null
      };
      
      // Insert based on priority
      if (priority === 'high') {
        queue.unshift(queueItem);
      } else {
        queue.push(queueItem);
      }
      
      // Start processing if not already running
      if (!isProcessing) {
        processQueue();
      }
      
      return queueItem.id;
    };
    
    const processQueue = async () => {
      if (isProcessing || queue.length === 0) {
        return;
      }
      
      isProcessing = true;
      
      while (queue.length > 0) {
        const item = queue.shift();
        
        try {
          await item.task();
        } catch (error) {
          console.warn('Queue task failed:', error);
        }
        
        // Yield periodically
        await this.yield();
      }
      
      isProcessing = false;
    };
    
    return { enqueue, getQueueLength: () => queue.length };
  }
  
  /**
   * Memory-efficient stream processor
   */
  async processStream(stream, processor, options = {}) {
    const config = { chunkSize: 1024, ...options };
    const results = [];
    
    const reader = stream.getReader();
    let chunk;
    
    try {
      while (!(chunk = await reader.read()).done) {
        const processed = await processor(chunk.value);
        results.push(processed);
        
        // Memory management
        if (results.length > config.chunkSize) {
          // Trigger garbage collection hint
          if (config.onChunkComplete) {
            config.onChunkComplete(results.splice(0, config.chunkSize));
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
    
    return results;
  }
}

export default AsyncProcessor;