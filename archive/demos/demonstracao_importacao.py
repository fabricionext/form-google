#!/usr/bin/env python3
"""
Demo da importação de dados da planilha Google Sheets
com a estrutura real fornecida pelo usuário.
"""

import os
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ID da planilha específica
PLANILHA_ID = "1Hj0D-VeJ51nQdAOBlvwzTKR_S3Sls40drthXfLI9Eow"


def get_sheets_service():
    """Obtém o serviço do Google Sheets."""
    try:
        service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not service_account_file:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON não configurado")
        
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        
        service = build("sheets", "v4", credentials=credentials)
        logger.info("Serviço Google Sheets inicializado com sucesso")
        return service
        
    except Exception as e:
        logger.error(f"Erro ao inicializar Google Sheets: {e}")
        raise


def buscar_dados_planilha(service, sheet_name: str = "Respostas") -> List[Dict]:
    """Busca dados da planilha."""
    try:
        range_name = f"{sheet_name}!A:ZZ"
        
        result = service.spreadsheets().values().get(
            spreadsheetId=PLANILHA_ID,
            range=range_name
        ).execute()
        
        values = result.get("values", [])
        if not values:
            logger.warning(f"Nenhum dado encontrado na aba '{sheet_name}'")
            return []
        
        headers = [str(header).strip() for header in values[0]]
        logger.info(f"Cabeçalhos encontrados na aba '{sheet_name}': {headers}")
        
        dados = []
        for i, row in enumerate(values[1:], start=2):
            while len(row) < len(headers):
                row.append("")
            
            linha_dict = {headers[j]: str(row[j]).strip() if j < len(row) else "" 
                         for j in range(len(headers))}
            
            if any(linha_dict.values()):
                linha_dict["_linha_original"] = i
                linha_dict["_aba_origem"] = sheet_name
                dados.append(linha_dict)
        
        logger.info(f"Total de {len(dados)} linhas de dados encontradas na aba '{sheet_name}'")
        return dados
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados da aba '{sheet_name}': {e}")
        raise


def limpar_documento(documento: str) -> str:
    """Remove formatação de documentos (CPF, CNPJ)."""
    if not documento:
        return ""
    return re.sub(r"[^\d]", "", documento)


def limpar_telefone(telefone: str) -> str:
    """Remove formatação de telefones."""
    if not telefone:
        return ""
    return re.sub(r"[^\d]", "", telefone)


def normalizar_nome(nome: str) -> str:
    """Normaliza nomes para capitalização correta."""
    if not nome:
        return ""
    return " ".join(word.capitalize() for word in nome.strip().split())


def montar_endereco_completo(dados_linha: Dict) -> str:
    """Monta endereço completo a partir dos campos separados."""
    partes_endereco = []
    
    # Logradouro
    logradouro = dados_linha.get("Endereço Logradouro", "").strip()
    if logradouro:
        partes_endereco.append(logradouro)
    
    # Número
    numero = dados_linha.get("Endereço Número", "").strip()
    if numero:
        partes_endereco.append(f"nº {numero}")
    
    # Complemento
    complemento = dados_linha.get("Endereço Complemento", "").strip()
    if complemento:
        partes_endereco.append(complemento)
    
    # Bairro
    bairro = dados_linha.get("Endereço Bairro", "").strip()
    if bairro:
        partes_endereco.append(f"- {bairro}")
    
    # Cidade
    cidade = dados_linha.get("Endereço Cidade", "").strip()
    if cidade:
        partes_endereco.append(f"- {cidade}")
    
    # UF
    uf = dados_linha.get("Endereço UF", "").strip()
    if uf:
        # Remove "PR - Paraná" -> "PR"
        uf_limpo = uf.split(" - ")[0] if " - " in uf else uf
        partes_endereco.append(f"/{uf_limpo}")
    
    # CEP
    cep = dados_linha.get("Endereço CEP", "").strip()
    if cep:
        partes_endereco.append(f"CEP: {cep}")
    
    return " ".join(partes_endereco)


def converter_data_brasileira(data_str: str) -> Optional[str]:
    """Converte data do formato brasileiro DD/MM/AAAA para formato ISO."""
    if not data_str:
        return None
    
    try:
        # Remove hora se existir
        data_apenas = data_str.split(" ")[0]
        
        # Converte DD/MM/AAAA para AAAA-MM-DD
        partes = data_apenas.split("/")
        if len(partes) == 3:
            dia, mes, ano = partes
            return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
    except:
        pass
    
    return None


def validate_cpf(cpf: str) -> tuple[bool, str]:
    """Valida CPF usando o algoritmo oficial."""
    if not cpf:
        return False, "CPF é obrigatório"
    
    cpf_digits = re.sub(r'\D', '', cpf)
    
    if len(cpf_digits) != 11:
        return False, "CPF deve ter 11 dígitos"
    
    if cpf_digits == cpf_digits[0] * 11:
        return False, "CPF inválido"
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf_digits[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_digits[9]) != dv1:
        return False, "CPF inválido"
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf_digits[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_digits[10]) != dv2:
        return False, "CPF inválido"
    
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Valida formato de email."""
    if not email:
        return False, "Email é obrigatório"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    return True, ""


def mapear_dados_para_cliente(dados_linha: Dict) -> Optional[Dict]:
    """Mapeia dados da planilha para o modelo Cliente."""
    try:
        dados_mapeados = {}
        
        # Email (obrigatório)
        email = dados_linha.get("Email", "").strip().lower()
        if not email:
            logger.warning(f"Linha {dados_linha.get('_linha_original', '?')}: Email não encontrado")
            return None
        
        dados_mapeados["email"] = email
        
        # Nome completo
        primeiro_nome = normalizar_nome(dados_linha.get("Primeiro Nome", ""))
        sobrenome = normalizar_nome(dados_linha.get("Sobrenome", ""))
        nome_completo = f"{primeiro_nome} {sobrenome}".strip()
        
        if not nome_completo:
            logger.warning(f"Linha {dados_linha.get('_linha_original', '?')}: Nome não encontrado")
            return None
        
        dados_mapeados["nome_completo"] = nome_completo
        
        # Documentos
        dados_mapeados["cpf"] = limpar_documento(dados_linha.get("CPF", ""))
        dados_mapeados["rg"] = dados_linha.get("RG Número", "").strip()
        dados_mapeados["rg_uf"] = dados_linha.get("RG UF Emissor", "").split(" - ")[0] if dados_linha.get("RG UF Emissor") else ""
        
        # Telefones
        dados_mapeados["telefone_celular"] = limpar_telefone(dados_linha.get("Telefone Celular", ""))
        dados_mapeados["telefone_fixo"] = limpar_telefone(dados_linha.get("Telefone Outro", ""))
        
        # Endereço completo
        endereco_completo = montar_endereco_completo(dados_linha)
        if endereco_completo:
            dados_mapeados["endereco"] = endereco_completo
        
        # Campos separados do endereço
        dados_mapeados["logradouro"] = dados_linha.get("Endereço Logradouro", "").strip()
        dados_mapeados["numero"] = dados_linha.get("Endereço Número", "").strip()
        dados_mapeados["complemento"] = dados_linha.get("Endereço Complemento", "").strip()
        dados_mapeados["bairro"] = dados_linha.get("Endereço Bairro", "").strip()
        dados_mapeados["cidade"] = dados_linha.get("Endereço Cidade", "").strip()
        
        # UF limpo
        uf_bruto = dados_linha.get("Endereço UF", "").strip()
        dados_mapeados["uf"] = uf_bruto.split(" - ")[0] if " - " in uf_bruto else uf_bruto
        
        dados_mapeados["cep"] = limpar_documento(dados_linha.get("Endereço CEP", ""))
        
        # Outros dados
        dados_mapeados["nacionalidade"] = dados_linha.get("Nacionalidade", "").strip()
        dados_mapeados["estado_civil"] = dados_linha.get("Estado Civil", "").strip()
        dados_mapeados["profissao"] = dados_linha.get("Profissão", "").strip()
        dados_mapeados["cnh"] = limpar_documento(dados_linha.get("CNH Número", ""))
        
        # Data de nascimento
        data_nascimento = converter_data_brasileira(dados_linha.get("Data Nascimento", ""))
        if data_nascimento:
            dados_mapeados["data_nascimento"] = data_nascimento
        
        # Data de registro
        data_registro = converter_data_brasileira(dados_linha.get("Data Hora Registro", ""))
        if data_registro:
            dados_mapeados["data_cadastro"] = data_registro
        
        dados_mapeados["tipo_pessoa"] = "FISICA"
        
        return dados_mapeados
        
    except Exception as e:
        logger.error(f"Erro ao mapear dados da linha {dados_linha.get('_linha_original', '?')}: {e}")
        return None


def simular_importacao_com_dados_exemplo():
    """Simula a importação usando os dados de exemplo fornecidos."""
    
    # Dados de exemplo baseados na estrutura fornecida
    dados_exemplo = [
        {
            "Data Hora Registro": "22/03/2023 10:01",
            "Primeiro Nome": "Taina",
            "Sobrenome": "Miranda Destro",
            "Nacionalidade": "Brasileiro(a)",
            "Estado Civil": "Casado(a)",
            "Profissão": "Do lar",
            "Endereço Logradouro": "R. Joaquim José de Almeida Filho, 152 - Centro",
            "Endereço Número": "",
            "Endereço Complemento": "",
            "Endereço Bairro": "",
            "Endereço Cidade": "Jandaia do Sul",
            "Endereço UF": "PR - Paraná",
            "Endereço CEP": "",
            "Telefone Celular": "(43) 99921-2123",
            "Telefone Outro": "",
            "Email": "taina@eamil.com",
            "Data Nascimento": "04/01/1987",
            "RG Número": "94390451",
            "RG UF Emissor": "PR - Paraná",
            "CPF": "050.440.219-62",
            "CNH Número": "04388699233",
            "_linha_original": 2,
            "_aba_origem": "Respostas"
        },
        {
            "Data Hora Registro": "23/03/2023 09:57",
            "Primeiro Nome": "Lucas",
            "Sobrenome": "Assis Raymundo",
            "Nacionalidade": "Brasileiro(a)",
            "Estado Civil": "Casado(a)",
            "Profissão": "Empresário",
            "Endereço Logradouro": "Rua Ernâni Lacerda de Athayde, 995 Apto 501",
            "Endereço Número": "",
            "Endereço Complemento": "",
            "Endereço Bairro": "",
            "Endereço Cidade": "Londrina",
            "Endereço UF": "PR - Paraná",
            "Endereço CEP": "86055-630",
            "Telefone Celular": "(43) 98801-1584",
            "Telefone Outro": "",
            "Email": "lucasassisraymundo@gmail.com",
            "Data Nascimento": "18/01/1989",
            "RG Número": "89667941",
            "RG UF Emissor": "PR - Paraná",
            "CPF": "075.327.969-06",
            "CNH Número": "04072549680",
            "_linha_original": 3,
            "_aba_origem": "Respostas"
        },
        {
            "Data Hora Registro": "24/03/2023 10:07",
            "Primeiro Nome": "Gerson",
            "Sobrenome": "Andre dos Santos",
            "Nacionalidade": "Brasileiro(a)",
            "Estado Civil": "Casado(a)",
            "Profissão": "Motorista Profissional",
            "Endereço Logradouro": "Rua Luiz Gonzaga, 15",
            "Endereço Número": "",
            "Endereço Complemento": "",
            "Endereço Bairro": "",
            "Endereço Cidade": "Londrina",
            "Endereço UF": "PR - Paraná",
            "Endereço CEP": "86082-025",
            "Telefone Celular": "(43) 99196-4165",
            "Telefone Outro": "",
            "Email": "gersonandre@882@gmail.com",  # Email com erro proposital
            "Data Nascimento": "18/07/1982",
            "RG Número": "78324791",
            "RG UF Emissor": "PR - Paraná",
            "CPF": "051.779.574-46",
            "CNH Número": "02402552823",
            "_linha_original": 4,
            "_aba_origem": "Respostas"
        }
    ]
    
    print("🔄 SIMULANDO IMPORTAÇÃO COM DADOS DE EXEMPLO...")
    print("-" * 60)
    
    estatisticas = {
        "total": len(dados_exemplo),
        "importados": 0,
        "duplicados": 0,
        "erros": 0
    }
    
    clientes_validos = []
    emails_processados = set()
    
    for dados_linha in dados_exemplo:
        try:
            print(f"\n📋 Processando linha {dados_linha['_linha_original']}:")
            print(f"   Nome: {dados_linha['Primeiro Nome']} {dados_linha['Sobrenome']}")
            print(f"   Email: {dados_linha['Email']}")
            print(f"   CPF: {dados_linha['CPF']}")
            
            dados_cliente = mapear_dados_para_cliente(dados_linha)
            if not dados_cliente:
                print("   ❌ Erro no mapeamento")
                estatisticas["erros"] += 1
                continue
            
            # Validação de email
            is_valid, error_msg = validate_email(dados_cliente["email"])
            if not is_valid:
                print(f"   ❌ Email inválido: {error_msg}")
                estatisticas["erros"] += 1
                continue
            
            # Validação de CPF
            if dados_cliente.get("cpf"):
                is_valid, error_msg = validate_cpf(dados_cliente["cpf"])
                if not is_valid:
                    print(f"   ❌ CPF inválido: {error_msg}")
                    estatisticas["erros"] += 1
                    continue
            
            # Verifica duplicados
            email = dados_cliente["email"]
            if email in emails_processados:
                print("   ⚠️  Email duplicado")
                estatisticas["duplicados"] += 1
                continue
            
            emails_processados.add(email)
            clientes_validos.append(dados_cliente)
            print("   ✅ Cliente válido para importação")
            estatisticas["importados"] += 1
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            estatisticas["erros"] += 1
    
    return estatisticas, clientes_validos


def main():
    """Função principal da demonstração."""
    try:
        print("=" * 70)
        print("🚀 DEMONSTRAÇÃO DE IMPORTAÇÃO DA PLANILHA")
        print("   (Baseada na estrutura real fornecida)")
        print("=" * 70)
        print(f"ID da planilha: {PLANILHA_ID}")
        print()
        
        # Primeira parte: simulação com dados de exemplo
        stats, clientes_validos = simular_importacao_com_dados_exemplo()
        
        # Mostra resultados da simulação
        print("\n" + "="*60)
        print("🎯 RESULTADOS DA SIMULAÇÃO")
        print("="*60)
        print(f"📊 Total de registros processados: {stats['total']}")
        print(f"✅ Clientes válidos para importação: {stats['importados']}")
        print(f"⚠️  Registros duplicados (ignorados): {stats['duplicados']}")
        print(f"❌ Registros com erro: {stats['erros']}")
        
        # Taxa de sucesso
        if stats['total'] > 0:
            taxa_sucesso = (stats['importados'] / stats['total']) * 100
            print(f"📈 Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        # Mostra estrutura dos clientes válidos
        if clientes_validos:
            print(f"\n👥 ESTRUTURA DOS CLIENTES VÁLIDOS:")
            print("-" * 50)
            for i, cliente in enumerate(clientes_validos, 1):
                print(f"\n{i}. {cliente['nome_completo']}")
                print(f"   📧 Email: {cliente['email']}")
                print(f"   🆔 CPF: {cliente.get('cpf', 'Não informado')}")
                print(f"   📱 Celular: {cliente.get('telefone_celular', 'Não informado')}")
                print(f"   🏠 Endereço: {cliente.get('endereco', 'Não informado')}")
                print(f"   📅 Data Nascimento: {cliente.get('data_nascimento', 'Não informada')}")
                print(f"   💼 Profissão: {cliente.get('profissao', 'Não informada')}")
        
        print("\n" + "="*60)
        print("📋 ESTRUTURA DE MAPEAMENTO IMPLEMENTADA:")
        print("="*60)
        print("✅ Campos principais mapeados:")
        print("   • Nome completo (Primeiro Nome + Sobrenome)")
        print("   • Email (validado)")
        print("   • CPF (validado e limpo)")
        print("   • Telefones (celular e fixo, limpos)")
        print("   • Endereço completo (montado a partir dos campos)")
        print("   • Campos de endereço separados (logradouro, número, etc.)")
        print("   • Documentos (RG, CNH)")
        print("   • Dados pessoais (profissão, estado civil, etc.)")
        print("   • Datas (nascimento e cadastro, convertidas)")
        
        print("\n⚠️  Observações sobre a importação:")
        print("   • Emails inválidos são rejeitados")
        print("   • CPFs são validados com algoritmo oficial")
        print("   • Endereços são montados automaticamente")
        print("   • Dados duplicados são identificados")
        print("   • Telefones são limpos (apenas números)")
        print("   • UF é extraído corretamente (PR em vez de 'PR - Paraná')")
        
        # Segunda parte: tenta acessar a planilha real (se possível)
        try:
            print("\n🌐 TENTANDO ACESSAR PLANILHA REAL...")
            service = get_sheets_service()
            dados_reais = buscar_dados_planilha(service, "Respostas")
            
            if dados_reais:
                print(f"✅ Planilha acessada com sucesso!")
                print(f"   Total de registros encontrados: {len(dados_reais)}")
                
                # Mostra amostra de cabeçalhos
                if dados_reais:
                    headers = [k for k in dados_reais[0].keys() if not k.startswith('_')]
                    print(f"   Cabeçalhos encontrados: {len(headers)} campos")
                    
                    # Simula uma pequena amostra
                    amostra = dados_reais[:10]
                    stats_real, _ = simular_importacao_com_dados_reais(amostra)
                    
                    print(f"\n📊 Teste com amostra de 10 registros:")
                    print(f"   ✅ Válidos: {stats_real['importados']}")
                    print(f"   ❌ Com erro: {stats_real['erros']}")
            
        except Exception as e:
            print(f"⚠️  Não foi possível acessar a planilha real: {e}")
        
        print("\n🎉 Para executar a importação real:")
        print("   1. Configure a conexão com o banco de dados PostgreSQL")
        print("   2. Execute: python import_planilha_especifica.py")
        print("   3. Escolha as abas e tabelas de destino")
        print("   4. Acompanhe o progresso da importação")
        print()
        print("✅ Demonstração concluída com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante a demonstração: {e}")
        raise


def simular_importacao_com_dados_reais(dados: List[Dict]) -> tuple[Dict[str, int], List[Dict]]:
    """Simula importação com dados reais da planilha."""
    estatisticas = {
        "total": len(dados),
        "importados": 0,
        "duplicados": 0,
        "erros": 0
    }
    
    emails_processados = set()
    clientes_validos = []
    
    for linha in dados:
        try:
            dados_cliente = mapear_dados_para_cliente(linha)
            if not dados_cliente:
                estatisticas["erros"] += 1
                continue
            
            # Validação de email
            if dados_cliente.get("email"):
                is_valid, _ = validate_email(dados_cliente["email"])
                if not is_valid:
                    estatisticas["erros"] += 1
                    continue
            
            # Validação de CPF
            if dados_cliente.get("cpf"):
                is_valid, _ = validate_cpf(dados_cliente["cpf"])
                if not is_valid:
                    estatisticas["erros"] += 1
                    continue
            
            # Verifica duplicados
            email = dados_cliente.get("email")
            if email in emails_processados:
                estatisticas["duplicados"] += 1
                continue
            
            if email:
                emails_processados.add(email)
            
            clientes_validos.append(dados_cliente)
            estatisticas["importados"] += 1
            
        except Exception as e:
            estatisticas["erros"] += 1
    
    return estatisticas, clientes_validos


if __name__ == "__main__":
    main() 