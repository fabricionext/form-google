"""
Serviço responsável por lógicas relacionadas aos formulários dinâmicos.
Extrai a complexidade das rotas, seguindo o princípio Single Responsibility.
"""

import re
from typing import Dict, List, Tuple, Any
from flask import current_app, abort
from datetime import datetime

from ..models import (
    FormularioGerado, 
    PeticaoModelo, 
    PeticaoPlaceholder
)


class FormularioService:
    """Service para gerenciar formulários dinâmicos"""
    
    def __init__(self, slug: str):
        self.slug = slug
        self._form_gerado = None
        self._modelo = None
        self._placeholders = None
    
    @property
    def form_gerado(self) -> FormularioGerado:
        """Lazy loading do formulário gerado"""
        if self._form_gerado is None:
            self._form_gerado = FormularioGerado.query.filter_by(slug=self.slug).first()
            if not self._form_gerado:
                current_app.logger.error(f"Formulário não encontrado para slug: {self.slug}")
                # Listar formulários disponíveis para debug
                todos_formularios = FormularioGerado.query.all()
                current_app.logger.info(f"Formulários disponíveis: {[f.slug for f in todos_formularios]}")
                abort(404, description=f"Formulário com slug '{self.slug}' não encontrado")
        return self._form_gerado
    
    @property 
    def modelo(self) -> PeticaoModelo:
        """Lazy loading do modelo"""
        if self._modelo is None:
            self._modelo = PeticaoModelo.query.get_or_404(self.form_gerado.modelo_id)
        return self._modelo
    
    @property
    def placeholders(self) -> List[PeticaoPlaceholder]:
        """Lazy loading dos placeholders"""
        if self._placeholders is None:
            self._placeholders = (
                PeticaoPlaceholder.query
                .filter_by(modelo_id=self.modelo.id)
                .order_by(PeticaoPlaceholder.ordem)
                .all()
            )
        return self._placeholders
    
    def agrupar_campos_por_categoria(self) -> Dict[str, Any]:
        """
        Organiza campos por categoria usando a função de categorização melhorada.
        Extrai toda a lógica complexa de categorização da rota.
        """
        # Importar dentro do método para evitar import circular
        from ..routes import categorize_placeholder_key
        
        campo_grupos = {
            "autores": {},  # Será preenchido com autores numerados
            "cliente": [],
            "endereco": [],
            "processo": [],
            "autoridades": [],
            "polo_ativo": [],
            "polo_passivo": [],
            "terceiros": [],
            "outros": [],
        }

        # Organizar campos por categoria
        for placeholder in self.placeholders:
            categoria = categorize_placeholder_key(placeholder.chave)
            chave_lower = placeholder.chave.lower()

            # Tratamento especial para autores numerados
            if categoria in ["autor_dados", "autor_endereco"]:
                match = re.match(r"autor_(\d+)_(.+)", chave_lower)
                if match:
                    autor_num = int(match.group(1))
                    if autor_num not in campo_grupos["autores"]:
                        campo_grupos["autores"][autor_num] = {"dados": [], "endereco": []}

                    if categoria == "autor_endereco":
                        campo_grupos["autores"][autor_num]["endereco"].append(placeholder.chave)
                    else:
                        campo_grupos["autores"][autor_num]["dados"].append(placeholder.chave)
                else:
                    # Autor sem numeração - adicionar aos dados do cliente
                    if "endereco" in chave_lower or "endereço" in chave_lower:
                        campo_grupos["endereco"].append(placeholder.chave)
                    else:
                        campo_grupos["cliente"].append(placeholder.chave)

            # Tratamento especial para autoridades
            elif categoria == "autoridades":
                campo_grupos["autoridades"].append(placeholder.chave)
            else:
                # Adicionar à categoria correspondente
                if categoria in campo_grupos:
                    # Verificação extra: se for campo de autoridade, sempre colocar em autoridades
                    if "orgao_transito" in chave_lower or "autoridade" in chave_lower:
                        campo_grupos["autoridades"].append(placeholder.chave)
                    else:
                        campo_grupos[categoria].append(placeholder.chave)
                else:
                    # Última verificação: campos não categorizados de autoridades
                    if "orgao_transito" in chave_lower or "autoridade" in chave_lower:
                        campo_grupos["autoridades"].append(placeholder.chave)
                    else:
                        campo_grupos["outros"].append(placeholder.chave)

        # Log da organização dos campos para debug
        self._log_organizacao_campos(campo_grupos)
        
        # Verificação e correção de campos de autoridades mal posicionados
        self._corrigir_campos_autoridades(campo_grupos)
        
        return campo_grupos
    
    def _log_organizacao_campos(self, campo_grupos: Dict[str, Any]) -> None:
        """Log detalhado da organização dos campos para debug"""
        current_app.logger.info(f"=== ORGANIZAÇÃO DOS CAMPOS ===")
        for categoria, campos in campo_grupos.items():
            if categoria == "autores":
                current_app.logger.info(f"Autores detectados: {list(campos.keys())}")
                for autor_num, autor_campos in campos.items():
                    current_app.logger.info(
                        f"  Autor {autor_num}: {len(autor_campos['dados'])} dados, "
                        f"{len(autor_campos['endereco'])} endereços"
                    )
            else:
                current_app.logger.info(
                    f"{categoria}: {len(campos) if isinstance(campos, list) else 0} campos"
                )
    
    def _corrigir_campos_autoridades(self, campo_grupos: Dict[str, Any]) -> None:
        """Corrige campos de autoridades que estão em categorias erradas"""
        for categoria, campos in campo_grupos.items():
            if categoria != "autoridades" and isinstance(campos, list):
                campos_autoridade = [c for c in campos if "orgao_transito" in c.lower()]
                if campos_autoridade:
                    current_app.logger.warning(
                        f"ATENÇÃO: Campos de autoridade encontrados em '{categoria}': {campos_autoridade}"
                    )
                    # Mover para autoridades
                    for campo in campos_autoridade:
                        campos.remove(campo)
                        campo_grupos["autoridades"].append(campo)
    
    def build_dynamic_form_class(self):
        """
        Constrói a classe do formulário dinâmico.
        Delega para a função existente para manter compatibilidade.
        """
        # Importar dentro do método para evitar import circular
        from ..routes import build_dynamic_form
        return build_dynamic_form(self.placeholders)
    
    def get_placeholder_analysis(self):
        """
        Analisa os placeholders e retorna informações detalhadas.
        Útil para debugging e alinhamento de formulários.
        """
        campos_organizados = self.agrupar_campos_por_categoria()
        
        analysis = {
            "total_placeholders": len(self.placeholders),
            "categorias": {},
            "personas_detectadas": {},
            "campos_sem_categoria": [],
            "sugestoes_melhoria": []
        }
        
        # Analisar cada categoria
        for categoria, campos in campos_organizados.items():
            if categoria == "autores":
                analysis["categorias"][categoria] = {
                    "total_autores": len(campos),
                    "autores_detalhes": {}
                }
                for autor_num, autor_data in campos.items():
                    analysis["categorias"][categoria]["autores_detalhes"][autor_num] = {
                        "dados": len(autor_data.get("dados", [])),
                        "endereco": len(autor_data.get("endereco", []))
                    }
            else:
                analysis["categorias"][categoria] = len(campos) if isinstance(campos, list) else 0
        
        # Detectar personas
        from ..routes import detect_persona_patterns
        chaves = [p.chave for p in self.placeholders]
        persona_analysis = detect_persona_patterns(chaves)
        analysis["personas_detectadas"] = persona_analysis
        
        # Identificar campos sem categoria
        outros_campos = campos_organizados.get("outros", [])
        if outros_campos:
            analysis["campos_sem_categoria"] = [campo.chave for campo in outros_campos]
        
        # Gerar sugestões
        analysis["sugestoes_melhoria"] = self._generate_improvement_suggestions(campos_organizados)
        
        return analysis
    
    def _generate_improvement_suggestions(self, campos_organizados):
        """Gera sugestões para melhorar o formulário."""
        sugestoes = []
        
        # Verificar se há campos órfãos
        if campos_organizados.get("outros"):
            sugestoes.append(f"{len(campos_organizados['outros'])} campos não categorizados - revisar categorização")
        
        # Verificar se há autores sem endereço
        autores = campos_organizados.get("autores", {})
        for autor_num, autor_data in autores.items():
            if autor_data.get("dados") and not autor_data.get("endereco"):
                sugestoes.append(f"Autor {autor_num} tem dados mas não tem endereço")
        
        # Verificar campos essenciais
        todos_campos = []
        for categoria, campos in campos_organizados.items():
            if categoria == "autores":
                for autor_data in campos.values():
                    todos_campos.extend(autor_data.get("dados", []))
                    todos_campos.extend(autor_data.get("endereco", []))
            elif isinstance(campos, list):
                todos_campos.extend(campos)
        
        chaves_essenciais = ["nome", "cpf", "endereco"]
        chaves_presentes = [campo.chave.lower() for campo in todos_campos]
        
        for essencial in chaves_essenciais:
            if not any(essencial in chave for chave in chaves_presentes):
                sugestoes.append(f"Campo essencial '{essencial}' pode estar faltando")
        
        return sugestoes
    
    def validate_placeholder_consistency(self):
        """
        Valida consistência entre placeholders do template e banco de dados.
        """
        try:
            # Extrair placeholders diretamente do documento Google
            from ..google_services import get_docs_service, extract_placeholders
            from ..utils import safe_extract_placeholder_keys
            
            docs_service = get_docs_service()
            placeholders_doc = extract_placeholders(docs_service, self.modelo.google_doc_id)
            chaves_doc = safe_extract_placeholder_keys(placeholders_doc)
            
            # Comparar com placeholders no banco
            chaves_db = [p.chave for p in self.placeholders]
            
            chaves_doc_set = set(chaves_doc)
            chaves_db_set = set(chaves_db)
            
            return {
                "consistency_check": True,
                "placeholders_doc": len(chaves_doc),
                "placeholders_db": len(chaves_db),
                "missing_in_db": list(chaves_doc_set - chaves_db_set),
                "extra_in_db": list(chaves_db_set - chaves_doc_set),
                "synchronized": chaves_doc_set == chaves_db_set
            }
            
        except Exception as e:
            current_app.logger.error(f"Erro na validação de consistência: {e}")
            return {
                "consistency_check": False,
                "error": str(e)
            } 