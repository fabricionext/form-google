"""
Serviço de análise de documentos Google Docs.
Extrai placeholders, analisa estrutura e obtém metadados.
"""

import re
import logging
from typing import Dict, List, Set, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict

from googleapiclient.errors import HttpError

from app.services.google_service_account import google_service_account
from app.services.cache_service import document_cache
from app.utils.exceptions import (
    GoogleDriveException,
    AuthenticationException,
    DocumentNotFoundException
)

logger = logging.getLogger(__name__)


class GoogleDocsAnalyzer:
    """
    Analisador de documentos Google Docs.
    
    Extrai placeholders, analisa estrutura e fornece insights
    sobre templates de documentos.
    """
    
    # Padrões de placeholder mais comuns
    PLACEHOLDER_PATTERNS = [
        r'\{\{([^}]+)\}\}',           # {{nome_placeholder}}
        r'\[\[([^\]]+)\]\]',          # [[nome_placeholder]]
        r'\{([^}]+)\}',               # {nome_placeholder}
        r'\[([^\]]+)\]',              # [nome_placeholder]
        r'<<([^>]+)>>',               # <<nome_placeholder>>
        r'%([^%]+)%',                 # %nome_placeholder%
        r'\$\{([^}]+)\}',             # ${nome_placeholder}
        r'#([A-Z_][A-Z0-9_]*)#',      # #NOME_PLACEHOLDER#
    ]
    
    # Categorias automáticas baseadas em padrões de nome
    CATEGORY_PATTERNS = {
        'cliente': [
            r'nome|cliente|razao|social|cpf|cnpj|rg|documento',
            r'endereco|logradouro|cidade|estado|cep|bairro',
            r'telefone|celular|email|contato',
            r'nascimento|idade|profissao|estado_civil'
        ],
        'juridico': [
            r'processo|numero|vara|comarca|juiz|advogado',
            r'peticao|requerimento|defesa|recurso',
            r'lei|artigo|paragrafo|inciso|codigo',
            r'prazo|audiencia|data_processo'
        ],
        'documento': [
            r'titulo|assunto|objeto|referencia',
            r'data|local|assinatura|testemunha',
            r'protocolo|registro|numero_documento'
        ],
        'financeiro': [
            r'valor|preco|custo|honorario|taxa',
            r'desconto|parcela|pagamento|vencimento',
            r'moeda|real|dolar|euro'
        ],
        'temporal': [
            r'data|dia|mes|ano|hora|minuto',
            r'prazo|periodo|inicio|fim|duracao',
            r'vencimento|agendamento'
        ]
    }
    
    def __init__(self):
        """Inicializa o analisador."""
        self.auth_service = google_service_account
    
    def analyze_document(self, user_id: str, document_id: str) -> Dict[str, Any]:
        """
        Analisa um documento Google Docs completo.
        
        Args:
            user_id: ID do usuário autenticado
            document_id: ID do documento no Google Drive
            
        Returns:
            Análise completa do documento
        """
        try:
            # Verifica cache primeiro
            cached_analysis = document_cache.get_analysis(document_id)
            if cached_analysis:
                logger.info(f"✅ Análise do documento {document_id} obtida do cache")
                return cached_analysis
            
            logger.info(f"Iniciando análise do documento {document_id} para usuário {user_id}")
            
            # Obtém serviços autenticados
            docs_service = self.auth_service.get_docs_service()
            drive_service = self.auth_service.get_drive_service()
            
            # Obtém conteúdo do documento
            document = docs_service.documents().get(documentId=document_id).execute()
            
            # Obtém metadados do Drive
            file_metadata = drive_service.files().get(
                fileId=document_id,
                fields='name,createdTime,modifiedTime,size,owners,permissions'
            ).execute()
            
            # Extrai texto completo
            full_text = self._extract_full_text(document)
            
            # Analisa placeholders
            placeholders_analysis = self._analyze_placeholders(full_text)
            
            # Analisa estrutura
            structure_analysis = self._analyze_structure(document)
            
            # Gera estatísticas
            statistics = self._generate_statistics(full_text, placeholders_analysis)
            
            analysis_result = {
                'document_id': document_id,
                'metadata': {
                    'name': file_metadata.get('name'),
                    'created_time': file_metadata.get('createdTime'),
                    'modified_time': file_metadata.get('modifiedTime'),
                    'size': file_metadata.get('size'),
                    'owners': file_metadata.get('owners', []),
                    'title': document.get('title')
                },
                'content': {
                    'full_text': full_text,
                    'word_count': len(full_text.split()),
                    'character_count': len(full_text),
                    'paragraph_count': len(document.get('body', {}).get('content', []))
                },
                'placeholders': placeholders_analysis,
                'structure': structure_analysis,
                'statistics': statistics,
                'analysis_timestamp': datetime.now().isoformat(),
                'suitable_for_template': self._assess_template_suitability(placeholders_analysis, statistics)
            }
            
            logger.info(f"Análise concluída: {len(placeholders_analysis.get('placeholders', []))} placeholders encontrados")
            
            # Armazena no cache (TTL: 2 horas)
            document_cache.set_analysis(document_id, analysis_result, ttl_minutes=120)
            logger.debug(f"Análise do documento {document_id} armazenada no cache")
            
            return analysis_result
            
        except HttpError as e:
            if e.resp.status == 404:
                raise DocumentNotFoundException(document_id)
            else:
                logger.error(f"Erro HTTP ao analisar documento: {e}")
                raise GoogleDriveException(f"Erro ao acessar documento: {e}")
                
        except Exception as e:
            logger.error(f"Erro inesperado na análise: {e}")
            raise GoogleDriveException(f"Falha na análise do documento: {e}")
    
    def _extract_full_text(self, document: Dict[str, Any]) -> str:
        """
        Extrai todo o texto de um documento Google Docs.
        
        Args:
            document: Documento do Google Docs
            
        Returns:
            Texto completo extraído
        """
        def extract_text_from_element(element):
            """Extrai texto de um elemento recursivamente."""
            text = ""
            
            if 'textRun' in element:
                text += element['textRun']['content']
            elif 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    text += extract_text_from_element(elem)
            elif 'table' in element:
                for row in element['table'].get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        for elem in cell.get('content', []):
                            text += extract_text_from_element(elem)
            
            return text
        
        full_text = ""
        body = document.get('body', {})
        
        for element in body.get('content', []):
            full_text += extract_text_from_element(element)
        
        return full_text
    
    def _analyze_placeholders(self, text: str) -> Dict[str, Any]:
        """
        Analisa placeholders no texto.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Análise dos placeholders encontrados
        """
        placeholders = []
        all_matches = set()
        pattern_stats = {}
        
        # Aplica cada padrão de placeholder
        for i, pattern in enumerate(self.PLACEHOLDER_PATTERNS):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            pattern_matches = []
            
            for match in matches:
                placeholder_name = match.group(1).strip()
                
                # Evita duplicatas
                if placeholder_name.lower() not in all_matches:
                    all_matches.add(placeholder_name.lower())
                    
                    placeholder_info = {
                        'name': placeholder_name,
                        'original_match': match.group(0),
                        'pattern_index': i,
                        'pattern': pattern,
                        'position': match.start(),
                        'category': self._categorize_placeholder(placeholder_name),
                        'type': self._infer_placeholder_type(placeholder_name),
                        'required': self._assess_required_field(placeholder_name),
                        'description': self._generate_description(placeholder_name)
                    }
                    
                    placeholders.append(placeholder_info)
                    pattern_matches.append(placeholder_info)
            
            pattern_stats[f'pattern_{i}'] = {
                'pattern': pattern,
                'matches': len(pattern_matches),
                'examples': [p['original_match'] for p in pattern_matches[:3]]
            }
        
        # Ordena por posição no documento
        placeholders.sort(key=lambda x: x['position'])
        
        return {
            'placeholders': placeholders,
            'total_count': len(placeholders),
            'unique_count': len(all_matches),
            'pattern_statistics': pattern_stats,
            'categories': self._group_by_category(placeholders),
            'types': self._group_by_type(placeholders)
        }
    
    def _categorize_placeholder(self, name: str) -> str:
        """
        Categoriza um placeholder baseado no nome.
        
        Args:
            name: Nome do placeholder
            
        Returns:
            Categoria identificada
        """
        name_lower = name.lower()
        
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower):
                    return category
        
        return 'geral'
    
    def _infer_placeholder_type(self, name: str) -> str:
        """
        Infere o tipo de campo baseado no nome.
        
        Args:
            name: Nome do placeholder
            
        Returns:
            Tipo de campo inferido
        """
        name_lower = name.lower()
        
        # Padrões para diferentes tipos
        type_patterns = {
            'email': r'email|e_mail|mail',
            'telefone': r'telefone|celular|phone|fone',
            'data': r'data|date|nascimento|vencimento',
            'numero': r'numero|number|cpf|cnpj|rg|processo',
            'endereco': r'endereco|address|logradouro|rua',
            'valor': r'valor|preco|price|custo|honorario',
            'texto_longo': r'observacao|descricao|detalhes|resumo',
            'selecao': r'tipo|categoria|status|estado',
            'booleano': r'ativo|habilitado|confirmado'
        }
        
        for field_type, pattern in type_patterns.items():
            if re.search(pattern, name_lower):
                return field_type
        
        return 'texto'
    
    def _assess_required_field(self, name: str) -> bool:
        """
        Avalia se um campo é obrigatório baseado no nome.
        
        Args:
            name: Nome do placeholder
            
        Returns:
            True se provavelmente obrigatório
        """
        name_lower = name.lower()
        
        # Campos tipicamente obrigatórios
        required_patterns = [
            r'nome|name',
            r'cpf|cnpj|documento',
            r'email|e_mail',
            r'data_nasc|nascimento',
            r'endereco|logradouro'
        ]
        
        for pattern in required_patterns:
            if re.search(pattern, name_lower):
                return True
        
        return False
    
    def _generate_description(self, name: str) -> str:
        """
        Gera descrição automática para um placeholder.
        
        Args:
            name: Nome do placeholder
            
        Returns:
            Descrição gerada
        """
        name_clean = name.replace('_', ' ').replace('-', ' ').title()
        category = self._categorize_placeholder(name)
        field_type = self._infer_placeholder_type(name)
        
        return f"{name_clean} ({category} - {field_type})"
    
    def _analyze_structure(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analisa a estrutura do documento.
        
        Args:
            document: Documento do Google Docs
            
        Returns:
            Análise da estrutura
        """
        body = document.get('body', {})
        content = body.get('content', [])
        
        structure = {
            'total_elements': len(content),
            'paragraphs': 0,
            'tables': 0,
            'lists': 0,
            'headings': 0,
            'images': 0,
            'has_header': False,
            'has_footer': False,
            'page_count': 1  # Estimativa básica
        }
        
        for element in content:
            if 'paragraph' in element:
                structure['paragraphs'] += 1
                
                # Verifica se é cabeçalho
                style = element['paragraph'].get('paragraphStyle', {})
                named_style = style.get('namedStyleType')
                if named_style and 'HEADING' in named_style:
                    structure['headings'] += 1
                    
            elif 'table' in element:
                structure['tables'] += 1
            elif 'tableOfContents' in element:
                structure['has_toc'] = True
        
        # Verifica headers e footers
        if document.get('headers'):
            structure['has_header'] = True
        if document.get('footers'):
            structure['has_footer'] = True
        
        return structure
    
    def _generate_statistics(self, text: str, placeholders_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera estatísticas sobre o documento.
        
        Args:
            text: Texto completo
            placeholders_analysis: Análise dos placeholders
            
        Returns:
            Estatísticas calculadas
        """
        words = text.split()
        
        return {
            'readability': {
                'word_count': len(words),
                'character_count': len(text),
                'average_word_length': sum(len(word) for word in words) / len(words) if words else 0,
                'sentence_count': len(re.findall(r'[.!?]+', text))
            },
            'placeholder_density': {
                'total_placeholders': placeholders_analysis['total_count'],
                'placeholders_per_100_words': (placeholders_analysis['total_count'] / len(words) * 100) if words else 0,
                'unique_placeholders': placeholders_analysis['unique_count']
            },
            'complexity': {
                'categories_used': len(placeholders_analysis['categories']),
                'field_types_used': len(placeholders_analysis['types']),
                'estimated_form_fields': placeholders_analysis['unique_count']
            }
        }
    
    def _assess_template_suitability(self, placeholders_analysis: Dict[str, Any], statistics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Avalia adequação do documento como template.
        
        Args:
            placeholders_analysis: Análise dos placeholders
            statistics: Estatísticas do documento
            
        Returns:
            Avaliação de adequação
        """
        score = 0
        max_score = 100
        reasons = []
        
        # Critério 1: Quantidade de placeholders (30 pontos)
        placeholder_count = placeholders_analysis['unique_count']
        if placeholder_count >= 10:
            score += 30
            reasons.append("Boa quantidade de placeholders (10+)")
        elif placeholder_count >= 5:
            score += 20
            reasons.append("Quantidade adequada de placeholders (5-9)")
        elif placeholder_count >= 1:
            score += 10
            reasons.append("Poucos placeholders (1-4)")
        else:
            reasons.append("Nenhum placeholder encontrado")
        
        # Critério 2: Diversidade de categorias (25 pontos)
        categories = len(placeholders_analysis['categories'])
        if categories >= 3:
            score += 25
            reasons.append("Boa diversidade de categorias")
        elif categories >= 2:
            score += 15
            reasons.append("Diversidade moderada de categorias")
        elif categories >= 1:
            score += 5
            reasons.append("Poucas categorias de placeholders")
        
        # Critério 3: Densidade de placeholders (20 pontos)
        density = statistics['placeholder_density']['placeholders_per_100_words']
        if 2 <= density <= 10:
            score += 20
            reasons.append("Densidade ideal de placeholders")
        elif 1 <= density < 2 or 10 < density <= 15:
            score += 10
            reasons.append("Densidade aceitável de placeholders")
        else:
            reasons.append("Densidade inadequada de placeholders")
        
        # Critério 4: Estrutura do documento (15 pontos)
        if placeholder_count > 0:
            score += 15
            reasons.append("Documento estruturado com campos variáveis")
        
        # Critério 5: Tamanho adequado (10 pontos)
        word_count = statistics['readability']['word_count']
        if 100 <= word_count <= 2000:
            score += 10
            reasons.append("Tamanho adequado para template")
        elif 50 <= word_count < 100 or 2000 < word_count <= 5000:
            score += 5
            reasons.append("Tamanho aceitável para template")
        
        # Determina classificação
        if score >= 80:
            classification = "Excelente"
        elif score >= 60:
            classification = "Bom"
        elif score >= 40:
            classification = "Regular"
        elif score >= 20:
            classification = "Baixo"
        else:
            classification = "Inadequado"
        
        return {
            'score': score,
            'max_score': max_score,
            'percentage': (score / max_score) * 100,
            'classification': classification,
            'suitable': score >= 40,
            'reasons': reasons,
            'recommendations': self._generate_recommendations(score, placeholders_analysis, statistics)
        }
    
    def _generate_recommendations(self, score: int, placeholders_analysis: Dict[str, Any], statistics: Dict[str, Any]) -> List[str]:
        """
        Gera recomendações para melhoria do template.
        
        Args:
            score: Pontuação obtida
            placeholders_analysis: Análise dos placeholders
            statistics: Estatísticas do documento
            
        Returns:
            Lista de recomendações
        """
        recommendations = []
        
        if placeholders_analysis['unique_count'] < 5:
            recommendations.append("Adicione mais campos variáveis usando {{nome_campo}}")
        
        if len(placeholders_analysis['categories']) < 2:
            recommendations.append("Diversifique as categorias de campos (cliente, jurídico, documento)")
        
        density = statistics['placeholder_density']['placeholders_per_100_words']
        if density < 1:
            recommendations.append("Aumente a densidade de placeholders no documento")
        elif density > 15:
            recommendations.append("Reduza a quantidade de placeholders para melhor legibilidade")
        
        if score < 40:
            recommendations.append("Considere revisar o documento para torná-lo mais adequado como template")
        
        return recommendations
    
    def _group_by_category(self, placeholders: List[Dict[str, Any]]) -> Dict[str, int]:
        """Agrupa placeholders por categoria."""
        categories = defaultdict(int)
        for placeholder in placeholders:
            categories[placeholder['category']] += 1
        return dict(categories)
    
    def _group_by_type(self, placeholders: List[Dict[str, Any]]) -> Dict[str, int]:
        """Agrupa placeholders por tipo."""
        types = defaultdict(int)
        for placeholder in placeholders:
            types[placeholder['type']] += 1
        return dict(types)
    
    def quick_scan(self, user_id: str, document_id: str) -> Dict[str, Any]:
        """
        Faz uma varredura rápida do documento para informações básicas.
        
        Args:
            user_id: ID do usuário autenticado
            document_id: ID do documento
            
        Returns:
            Informações básicas do documento
        """
        try:
            # Verifica cache primeiro
            cached_scan = document_cache.get_quick_scan(document_id)
            if cached_scan:
                logger.debug(f"✅ Quick scan do documento {document_id} obtido do cache")
                return cached_scan
            
            # Obtém apenas metadados do Drive
            drive_service = self.auth_service.get_drive_service()
            
            file_metadata = drive_service.files().get(
                fileId=document_id,
                fields='name,createdTime,modifiedTime,size,mimeType'
            ).execute()
            
            # Verifica se é um Google Doc
            is_google_doc = file_metadata.get('mimeType') == 'application/vnd.google-apps.document'
            
            scan_result = {
                'document_id': document_id,
                'name': file_metadata.get('name'),
                'is_google_doc': is_google_doc,
                'size': file_metadata.get('size'),
                'modified_time': file_metadata.get('modifiedTime'),
                'scannable': is_google_doc,
                'quick_scan': True
            }
            
            # Armazena no cache (TTL: 30 minutos)
            document_cache.set_quick_scan(document_id, scan_result, ttl_minutes=30)
            logger.debug(f"Quick scan do documento {document_id} armazenado no cache")
            
            return scan_result
            
        except HttpError as e:
            if e.resp.status == 404:
                raise DocumentNotFoundException(document_id)
            else:
                raise GoogleDriveException(f"Erro ao acessar documento: {e}")


# Instância global do analisador
google_docs_analyzer = GoogleDocsAnalyzer()