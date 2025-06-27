"""
Document Utilities
==================

Funções utilitárias para manipulação de documentos Google Docs.
Migradas do routes.py para melhor organização.
"""

import re
from typing import Dict, List, Any
from flask import current_app

from .placeholder_utils import detect_persona_patterns


def extract_placeholders_from_document(document: Dict[str, Any]) -> List[str]:
    """
    Extrai placeholders de um documento do Google Docs.
    Procura por padrões {{placeholder}} no texto.
    
    Migrado do routes.py com melhorias.
    """
    placeholders = []

    def extract_text_from_content(content):
        """Extrai texto de elementos de conteúdo do documento."""
        text = ""
        if "paragraph" in content:
            paragraph = content["paragraph"]
            if "elements" in paragraph:
                for element in paragraph["elements"]:
                    if "textRun" in element and "content" in element["textRun"]:
                        text += element["textRun"]["content"]
        elif "table" in content:
            # Processar tabelas também
            table = content["table"]
            if "tableRows" in table:
                for row in table["tableRows"]:
                    if "tableCells" in row:
                        for cell in row["tableCells"]:
                            if "content" in cell:
                                for cell_content in cell["content"]:
                                    text += extract_text_from_content(cell_content)
        return text

    # Processar o documento
    if "body" in document and "content" in document["body"]:
        full_text = ""
        for content in document["body"]["content"]:
            full_text += extract_text_from_content(content)

        # Buscar placeholders no formato {{placeholder}}
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(placeholder_pattern, full_text)
        
        for match in matches:
            # Limpar o placeholder (remover espaços extras)
            placeholder = match.strip()
            if placeholder and placeholder not in placeholders:
                placeholders.append(placeholder)

    current_app.logger.info(f"Extraídos {len(placeholders)} placeholders do documento")
    return placeholders


def extract_placeholders_keys_only(document: Dict[str, Any]) -> List[str]:
    """
    Extrai apenas as chaves dos placeholders, garantindo retorno de strings.
    
    Migrado do routes.py com melhorias na robustez.
    """
    try:
        placeholders = extract_placeholders_from_document(document)
        
        # Garantir que retornamos apenas strings válidas
        chaves_strings = []
        for placeholder in placeholders:
            if isinstance(placeholder, str) and placeholder.strip():
                chaves_strings.append(placeholder.strip())
            elif isinstance(placeholder, dict) and 'key' in placeholder:
                chaves_strings.append(str(placeholder['key']).strip())
            elif isinstance(placeholder, dict) and 'chave' in placeholder:
                chaves_strings.append(str(placeholder['chave']).strip())
        
        return chaves_strings
        
    except Exception as e:
        current_app.logger.error(f"Erro ao extrair placeholders: {e}")
        return []


def generate_preview_html(form_data: Dict[str, Any], modelo_nome: str = "") -> str:
    """
    Gera HTML de prévia do documento baseado nos dados do formulário.
    
    Migrado do routes.py com melhorias na formatação.
    """
    try:
        # Cabeçalho da prévia
        preview_html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Prévia do Documento</title>
            <style>
                body {{
                    font-family: 'Times New Roman', serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 20px;
                }}
                .section {{
                    margin-bottom: 25px;
                }}
                .section-title {{
                    font-weight: bold;
                    font-size: 16px;
                    color: #333;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 5px;
                    margin-bottom: 15px;
                }}
                .field-group {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-bottom: 15px;
                }}
                .field {{
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }}
                .field-label {{
                    font-weight: bold;
                    color: #555;
                }}
                .field-value {{
                    margin-top: 3px;
                }}
                @media print {{
                    body {{ margin: 0; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{modelo_nome or 'Documento Gerado'}</h1>
                <p>Prévia do documento a ser criado</p>
            </div>
        """
        
        # Organizar campos por categoria
        categorias = {
            'Dados Pessoais': [],
            'Endereço': [],
            'Dados Processuais': [],
            'Autoridades': [],
            'Outros': []
        }
        
        for field_name, field_value in form_data.items():
            if not field_value or field_name == 'csrf_token':
                continue
                
            # Determinar categoria
            field_lower = field_name.lower()
            if any(term in field_lower for term in ['nome', 'cpf', 'rg', 'email', 'telefone', 'nascimento']):
                categoria = 'Dados Pessoais'
            elif any(term in field_lower for term in ['endereco', 'cep', 'logradouro', 'bairro', 'cidade']):
                categoria = 'Endereço'
            elif any(term in field_lower for term in ['processo', 'comarca', 'vara', 'data_fato']):
                categoria = 'Dados Processuais'
            elif any(term in field_lower for term in ['autoridade', 'orgao', 'detran']):
                categoria = 'Autoridades'
            else:
                categoria = 'Outros'
            
            # Formatar label
            label = field_name.replace('_', ' ').title()
            label = label.replace('Cpf', 'CPF').replace('Rg', 'RG').replace('Cep', 'CEP')
            
            categorias[categoria].append({
                'label': label,
                'value': str(field_value)
            })
        
        # Gerar HTML das seções
        for categoria, campos in categorias.items():
            if campos:  # Só mostrar categoria se tiver campos
                preview_html += f"""
                <div class="section">
                    <div class="section-title">{categoria}</div>
                    <div class="field-group">
                """
                
                for campo in campos:
                    preview_html += f"""
                        <div class="field">
                            <div class="field-label">{campo['label']}</div>
                            <div class="field-value">{campo['value']}</div>
                        </div>
                    """
                
                preview_html += """
                    </div>
                </div>
                """
        
        # Rodapé
        preview_html += """
            <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #888;">
                <p>Esta é uma prévia do documento. O documento final será gerado no Google Docs.</p>
            </div>
        </body>
        </html>
        """
        
        return preview_html
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar prévia HTML: {e}")
        return f"<p>Erro ao gerar prévia: {str(e)}</p>"


def analyze_document_personas(document: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analisa personas em um documento Google Docs.
    
    Nova função para análise detalhada de personas em documentos.
    """
    try:
        # Extrair placeholders
        placeholders = extract_placeholders_keys_only(document)
        
        # Detectar personas
        persona_analysis = detect_persona_patterns(placeholders)
        
        # Análise adicional
        analysis = {
            'document_analysis': {
                'total_placeholders': len(placeholders),
                'unique_placeholders': len(set(placeholders)),
                'placeholder_list': placeholders
            },
            'persona_analysis': persona_analysis,
            'recommendations': []
        }
        
        # Gerar recomendações
        if persona_analysis['total_personas'] == 0:
            analysis['recommendations'].append(
                "Nenhuma persona detectada. Considere usar padrões como 'autor_1_nome', 'reu_1_cpf'."
            )
        elif persona_analysis['total_personas'] > 20:
            analysis['recommendations'].append(
                "Muitas personas detectadas. Considere simplificar o documento."
            )
        
        # Verificar consistência
        for persona_tipo, patterns in persona_analysis['patterns'].items():
            if len(patterns) > 1:
                for numero, campos in patterns.items():
                    if len(campos) < 2:
                        analysis['recommendations'].append(
                            f"Persona {persona_tipo}_{numero} tem poucos campos. "
                            f"Considere adicionar mais informações."
                        )
        
        return analysis
        
    except Exception as e:
        current_app.logger.error(f"Erro na análise de personas do documento: {e}")
        return {
            'error': str(e),
            'document_analysis': {'total_placeholders': 0},
            'persona_analysis': {'total_personas': 0},
            'recommendations': ['Erro na análise - verificar logs']
        }