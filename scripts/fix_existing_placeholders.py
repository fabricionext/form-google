#!/usr/bin/env python3
"""
Script para corrigir placeholders existentes no banco de dados.
Remove caracteres inválidos e normaliza formatos.
"""

def clean_placeholder_key_simple(chave):
    """Versão simples da função de limpeza para uso sem dependências."""
    import re
    
    if not isinstance(chave, str):
        chave = str(chave)
    
    # Remover caracteres especiais, manter apenas letras, números e underscore
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', chave.strip())
    
    # Remover underscores múltiplos consecutivos
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remover underscore do início e fim
    cleaned = cleaned.strip('_')
    
    return cleaned if cleaned else 'placeholder'

def generate_sql_update_script():
    """Gera script SQL para corrigir placeholders existentes."""
    
    print("-- Script SQL para corrigir placeholders existentes")
    print("-- Execute este script no banco de dados PostgreSQL")
    print()
    
    print("-- 1. Backup da tabela antes das alterações")
    print("CREATE TABLE peticao_placeholders_backup AS SELECT * FROM peticao_placeholders;")
    print()
    
    print("-- 2. Função para limpar chaves de placeholders")
    print("""
CREATE OR REPLACE FUNCTION clean_placeholder_key(input_key TEXT) 
RETURNS TEXT AS $$
BEGIN
    -- Remover caracteres especiais, manter apenas letras, números e underscore
    input_key := regexp_replace(trim(input_key), '[^a-zA-Z0-9_]', '_', 'g');
    
    -- Remover underscores múltiplos consecutivos
    input_key := regexp_replace(input_key, '_+', '_', 'g');
    
    -- Remover underscore do início e fim
    input_key := trim(input_key, '_');
    
    -- Se ficou vazio, usar placeholder padrão
    IF input_key = '' THEN
        input_key := 'placeholder';
    END IF;
    
    RETURN input_key;
END;
$$ LANGUAGE plpgsql;
    """)
    print()
    
    print("-- 3. Atualizar chaves problemáticas")
    print("""
UPDATE peticao_placeholders 
SET chave = clean_placeholder_key(chave)
WHERE chave ~ '[^a-zA-Z0-9_]' OR chave LIKE '_%' OR chave LIKE '%_';
    """)
    print()
    
    print("-- 4. Verificar resultados")
    print("""
SELECT 
    COUNT(*) as total_placeholders,
    COUNT(CASE WHEN chave ~ '[^a-zA-Z0-9_]' THEN 1 END) as chaves_invalidas,
    COUNT(CASE WHEN chave = '' THEN 1 END) as chaves_vazias
FROM peticao_placeholders;
    """)
    print()
    
    print("-- 5. Remover função temporária")
    print("DROP FUNCTION IF EXISTS clean_placeholder_key(TEXT);")
    print()
    
    print("-- 6. Se tudo estiver correto, remover backup")
    print("-- DROP TABLE peticao_placeholders_backup;")

def show_prevention_measures():
    """Mostra medidas preventivas implementadas."""
    
    print("=== MEDIDAS PREVENTIVAS IMPLEMENTADAS ===")
    print()
    
    print("1. ✅ Função safe_extract_placeholder_keys()")
    print("   - Normaliza dados de entrada (dicts ou strings)")
    print("   - Evita erro 'unhashable type: dict'")
    print("   - Retorna sempre lista de strings")
    print()
    
    print("2. ✅ Função clean_placeholder_key()")
    print("   - Remove caracteres especiais")
    print("   - Normaliza underscores")
    print("   - Valida formato final")
    print()
    
    print("3. ✅ Função handle_placeholder_extraction_error()")
    print("   - Tratamento robusto de erros")
    print("   - Mensagens amigáveis para usuário")
    print("   - Logging detalhado para debug")
    print()
    
    print("4. ✅ Melhorias na sincronização:")
    print("   - Validação de entrada")
    print("   - Limpeza automática de chaves")
    print("   - Skip de placeholders inválidos")
    print("   - Logging de operações")
    print()
    
    print("5. ✅ Google Services atualizado:")
    print("   - Usa extract_placeholders_keys_only()")
    print("   - Retorna apenas strings")
    print("   - Compatibilidade garantida")
    print()

def main():
    print("=== CORREÇÃO DE PLACEHOLDERS EXISTENTES ===")
    print()
    
    print("Este script ajuda a corrigir problemas em placeholders existentes")
    print("que podem causar erro 'unhashable type: dict' no futuro.")
    print()
    
    generate_sql_update_script()
    print()
    show_prevention_measures()
    
    print()
    print("=== INSTRUÇÕES DE USO ===")
    print()
    print("1. Faça backup do banco de dados")
    print("2. Execute o script SQL gerado acima")
    print("3. Teste a sincronização de placeholders")
    print("4. Monitore logs para novos problemas")
    print()
    print("⚠️  IMPORTANTE: Sempre faça backup antes de executar!")

if __name__ == "__main__":
    main()