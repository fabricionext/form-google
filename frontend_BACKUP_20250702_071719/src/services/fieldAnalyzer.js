// services/fieldAnalyzer.js
/**
 * Optimized field analysis with caching and performance improvements
 */
class FieldAnalyzer {
  constructor() {
    this.typeCache = new Map();
    this.compiledPatterns = this.compilePatterns();
    this.maxCacheSize = 1000;
  }
  
  /**
   * Pre-compile regex patterns for better performance
   */
  compilePatterns() {
    const patterns = {
      cpf: /cpf|documento|registro/i,
      cnpj: /cnpj|empresa|razao\.?social/i,
      email: /email|e-mail|correio/i,
      phone: /telefone|celular|contato|fone/i,
      date: /data|nascimento|vencimento|prazo/i,
      money: /valor|preco|salario|renda|quantia|r\$|real/i,
      cep: /cep|codigo\.?postal/i,
      process_number: /processo|numero\.?processo|n[ºª].*processo/i,
      law_article: /artigo|art\.|lei|codigo|inciso/i,
      textarea: /observa|descri|motivo|justifica|relato/i,
      select: /estado|sexo|categoria|tipo|natureza/i,
      boolean: /aceita|concorda|declara|sim.*nao/i
    };
    
    // Pre-compile all patterns
    const compiled = new Map();
    Object.entries(patterns).forEach(([key, pattern]) => {
      compiled.set(key, pattern);
    });
    
    return compiled;
  }
  
  /**
   * Optimized field type inference with caching
   */
  inferFieldType(fieldName, context) {
    // Create cache key (limit context to avoid memory bloat)
    const cacheKey = `${fieldName}:${context.substring(0, 50)}`;
    
    // Check cache first
    if (this.typeCache.has(cacheKey)) {
      return this.typeCache.get(cacheKey);
    }
    
    // Evict LRU if cache is full
    if (this.typeCache.size >= this.maxCacheSize) {
      this.evictLRU();
    }
    
    const searchText = `${fieldName} ${context}`.toLowerCase();
    let inferredType = 'text'; // default
    
    // Test compiled patterns
    for (const [type, pattern] of this.compiledPatterns) {
      if (pattern.test(searchText)) {
        inferredType = type;
        break; // Return first match for performance
      }
    }
    
    // Additional context analysis (only if no pattern match)
    if (inferredType === 'text') {
      inferredType = this.analyzeContext(context);
    }
    
    // Cache result
    this.typeCache.set(cacheKey, inferredType);
    
    return inferredType;
  }
  
  /**
   * Context analysis without regex (faster)
   */
  analyzeContext(context) {
    // Quick string checks (faster than regex)
    if (context.includes('R$')) return 'money';
    if (context.includes('/') && context.match(/\d{2}\/\d{2}\/\d{4}/)) return 'date';
    if (context.length > 100) return 'textarea';
    
    return 'text';
  }
  
  /**
   * LRU eviction for cache management
   */
  evictLRU() {
    // Simple eviction: remove 20% of cache
    const keysToRemove = Math.floor(this.typeCache.size * 0.2);
    const keys = Array.from(this.typeCache.keys());
    
    for (let i = 0; i < keysToRemove; i++) {
      this.typeCache.delete(keys[i]);
    }
  }
  
  /**
   * Clear cache (for memory management)
   */
  clearCache() {
    this.typeCache.clear();
  }
  
  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      size: this.typeCache.size,
      maxSize: this.maxCacheSize,
      usage: (this.typeCache.size / this.maxCacheSize * 100).toFixed(2) + '%'
    };
  }
}

export default FieldAnalyzer;