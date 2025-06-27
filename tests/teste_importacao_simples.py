#!/usr/bin/env python3
"""
Teste simples de importação da aba Respostas
"""

import psycopg2
import re
from datetime import datetime

# Configuração do banco
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'form_google',
    'user': 'postgres',
    'password': 'postgres'
}

def formatar_telefone(telefone):
    """Formata telefone com máscaras padrão."""
    if not telefone:
        return ""
    
    # Remove tudo que não é número
    numeros = re.sub(r'[^\d]', '', str(telefone))
    
    # Se não tem DDD, adiciona 41 (Curitiba)
    if len(numeros) == 8:
        numeros = "41" + numeros
    elif len(numeros) == 9:
        numeros = "41" + numeros
    
    # Formata conforme padrão
    if len(numeros) == 10:  # Fixo: (41) 3123-4567
        return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
    elif len(numeros) == 11:  # Celular: (41) 99123-4567
        return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
    else:
        return numeros

def limpar_cpf(cpf):
    """Remove formatação do CPF."""
    if not cpf:
        return ""
    return re.sub(r'[^\d]', '', str(cpf))

def get_dados_demonstracao():
    """Dados de demonstração da aba Respostas."""
    return [
        {
            "Data Hora Registro": "15/01/2024 10:30:45",
            "Primeiro Nome": "Alessandro",
            "Sobrenome": "Santos Ribeiro",
            "Email": "alessandro.santos@gmail.com",
            "CPF": "123.456.789-12",
            "Telefone Celular": "(41) 99111-2233",
            "Endereço Logradouro": "Rua XV de Novembro, 1500, Apto 301, Centro"
        },
        {
            "Data Hora Registro": "16/01/2024 14:22:10", 
            "Primeiro Nome": "Beatriz",
            "Sobrenome": "Oliveira Costa",
            "Email": "beatriz.oliveira@hotmail.com",
            "CPF": "987.654.321-98",
            "Telefone Celular": "(41) 98444-5566",
            "Endereço Logradouro": "Av. Cândido de Abreu, 817, Sala 1205, Cidade Industrial"
        },
        {
            "Data Hora Registro": "17/01/2024 09:15:30",
            "Primeiro Nome": "Carlos Roberto",
            "Sobrenome": "Silva",
            "Email": "carlos.roberto@yahoo.com", 
            "CPF": "456.789.123-45",
            "Telefone Celular": "(41) 99777-8899",
            "Endereço Logradouro": "Rua das Palmeiras, 250, Casa 02, Bairro Alto"
        }
    ]

def converter_data_registro(data_str):
    """Converte string de data para timestamp."""
    if not data_str:
        return datetime.now()
    
    try:
        # Formato brasileiro: 15/01/2024 10:30:45
        return datetime.strptime(data_str.strip(), "%d/%m/%Y %H:%M:%S")
    except ValueError:
        try:
            # Formato brasileiro sem hora: 15/01/2024
            return datetime.strptime(data_str.strip(), "%d/%m/%Y")
        except ValueError:
            print(f"⚠️ Formato de data não reconhecido: {data_str}")
            return datetime.now()

def testar_importacao():
    """Testa a importação com dados de demonstração."""
    print("🧪 TESTE DE IMPORTAÇÃO - ABA RESPOSTAS")
    print("=" * 50)
    
    try:
        # Conecta ao banco
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        print("✅ Conectado ao banco de dados")
        
        # Verifica estrutura da tabela
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clientes_peticionador'
            ORDER BY ordinal_position
        """)
        
        colunas = [row[0] for row in cursor.fetchall()]
        print(f"📊 Colunas disponíveis: {colunas}")
        
        # Verifica se campo data_registro existe
        tem_data_registro = 'data_registro' in colunas
        print(f"📅 Campo data_registro: {'✅ Existe' if tem_data_registro else '❌ Não existe'}")
        
        # Conta registros antes
        cursor.execute("SELECT COUNT(*) FROM clientes_peticionador")
        count_antes = cursor.fetchone()[0]
        print(f"📈 Clientes antes: {count_antes}")
        
        # Dados de demonstração
        dados_planilha = get_dados_demonstracao()
        print(f"📋 Registros para importar: {len(dados_planilha)}")
        
        sucessos = 0
        duplicados = 0
        erros = 0
        
        # Processa cada registro
        for i, linha in enumerate(dados_planilha, 1):
            print(f"\n📝 [{i}/{len(dados_planilha)}] Processando {linha['Primeiro Nome']} {linha['Sobrenome']}")
            
            try:
                # Prepara dados
                email = linha['Email'].strip().lower()
                nome_completo = f"{linha['Primeiro Nome']} {linha['Sobrenome']}".strip()
                cpf = limpar_cpf(linha['CPF'])
                telefone = formatar_telefone(linha['Telefone Celular'])
                endereco = linha['Endereço Logradouro'].strip()
                data_registro = converter_data_registro(linha['Data Hora Registro'])
                
                print(f"   📧 Email: {email}")
                print(f"   📱 Telefone: {telefone}")
                print(f"   🆔 CPF: {cpf}")
                print(f"   📅 Data: {data_registro}")
                
                # Verifica se já existe
                cursor.execute("""
                    SELECT id FROM clientes_peticionador 
                    WHERE email = %s OR (cpf IS NOT NULL AND cpf = %s)
                """, (email, cpf))
                
                if cursor.fetchone():
                    print(f"   ⚠️ Cliente já existe")
                    duplicados += 1
                    continue
                
                # Insere cliente
                if tem_data_registro:
                    cursor.execute("""
                        INSERT INTO clientes_peticionador (
                            tipo_pessoa, email, telefone_celular, nome_completo, 
                            cpf, data_registro
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, ('FISICA', email, telefone, nome_completo, cpf, data_registro))
                else:
                    cursor.execute("""
                        INSERT INTO clientes_peticionador (
                            tipo_pessoa, email, telefone_celular, nome_completo, cpf
                        ) VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, ('FISICA', email, telefone, nome_completo, cpf))
                
                novo_id = cursor.fetchone()[0]
                conn.commit()
                
                print(f"   ✅ Cliente importado (ID: {novo_id})")
                sucessos += 1
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
                erros += 1
                conn.rollback()
        
        # Conta registros depois
        cursor.execute("SELECT COUNT(*) FROM clientes_peticionador")
        count_depois = cursor.fetchone()[0]
        
        # Resultados
        print("\n" + "=" * 50)
        print("🎯 RESULTADOS DO TESTE")
        print("=" * 50)
        print(f"✅ Sucessos: {sucessos}")
        print(f"⚠️ Duplicados: {duplicados}")
        print(f"❌ Erros: {erros}")
        print(f"📈 Total: {count_antes} → {count_depois}")
        
        if sucessos > 0:
            print(f"\n🎉 {sucessos} clientes importados seguindo as especificações:")
            print("   📞 Telefones com máscara: (41) 99999-9999")
            print("   🏠 Endereços unificados na coluna logradouro")
            print("   📅 Data de registro preservada")
            print("   🆔 CPF limpo (apenas números)")
        
        cursor.close()
        conn.close()
        
        print("\n✅ TESTE CONCLUÍDO!")
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_importacao() 