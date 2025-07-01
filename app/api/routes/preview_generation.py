"""
Rotas para geração de previews dinâmicos de formulários.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from typing import Dict, Any, List, Optional
import traceback

from app.services.template_converter import template_converter
from app.services.preview_generator import preview_generator
from app.services.cache_service import document_cache
from app.utils.exceptions import (
    DocumentNotFoundException,
    ValidationException,
    TemplateServiceException
)
from app.extensions import limiter

logger = logging.getLogger(__name__)

# Blueprint para geração de previews
preview_generation_bp = Blueprint('preview_generation', __name__, url_prefix='/api/preview')


@preview_generation_bp.route('/generate/<document_id>', methods=['POST'])
@limiter.limit("5 per minute")
@login_required
def generate_form_preview(document_id):
    """
    Gera preview dinâmico de um formulário baseado em template.
    
    Args:
        document_id: ID do documento/template no Google Drive
        
    Request Body:
        {
            "layout": "single_column|two_column|grouped|wizard",
            "theme": "default|modern|compact",
            "include_sample_data": true,
            "template_name": "Nome personalizado (opcional)",
            "template_category": "Categoria personalizada (opcional)"
        }
        
    Returns:
        JSON com preview do formulário
    """
    try:
        user_id = str(current_user.id)
        data = request.get_json() or {}
        
        layout = data.get('layout', 'single_column')
        theme = data.get('theme', 'default')
        include_sample_data = data.get('include_sample_data', True)
        template_name = data.get('template_name')
        template_category = data.get('template_category')
        
        # Valida parâmetros
        valid_layouts = ['single_column', 'two_column', 'grouped', 'wizard']
        valid_themes = ['default', 'modern', 'compact']
        
        if layout not in valid_layouts:
            return jsonify({
                'success': False,
                'error': 'invalid_layout',
                'message': f'Layout deve ser um de: {", ".join(valid_layouts)}'
            }), 400
        
        if theme not in valid_themes:
            return jsonify({
                'success': False,
                'error': 'invalid_theme',
                'message': f'Tema deve ser um de: {", ".join(valid_themes)}'
            }), 400
        
        logger.info(f"Gerando preview do formulário {document_id} (layout: {layout}, tema: {theme})")
        
        # Converte documento em template
        converted_template = template_converter.convert_document_to_template(
            user_id=user_id,
            document_id=document_id,
            template_name=template_name,
            template_category=template_category
        )
        
        # Gera preview do formulário
        form_preview = preview_generator.generate_form_preview(
            template=converted_template,
            layout=layout,
            theme=theme,
            include_sample_data=include_sample_data
        )
        
        return jsonify({
            'success': True,
            'preview': form_preview,
            'generation_info': {
                'document_id': document_id,
                'layout': layout,
                'theme': theme,
                'field_count': len(converted_template.fields),
                'estimated_complexity': form_preview['preview_metadata']['complexity']
            },
            'message': f'Preview gerado com sucesso: {len(converted_template.fields)} campos'
        }), 200
        
    except DocumentNotFoundException:
        logger.warning(f"Documento não encontrado: {document_id}")
        return jsonify({
            'success': False,
            'error': 'document_not_found',
            'message': f'Documento {document_id} não foi encontrado'
        }), 404
        
    except ValidationException as e:
        logger.warning(f"Documento inadequado para preview: {e}")
        return jsonify({
            'success': False,
            'error': 'document_unsuitable',
            'message': str(e)
        }), 400
        
    except TemplateServiceException as e:
        logger.error(f"Erro no serviço de template: {e}")
        return jsonify({
            'success': False,
            'error': 'template_service_error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Erro inesperado na geração de preview: {e}")
        return jsonify({
            'success': False,
            'error': 'preview_generation_error',
            'message': 'Erro interno na geração de preview'
        }), 500


@preview_generation_bp.route('/quick/<document_id>', methods=['GET'])
@limiter.limit("10 per minute")
@login_required
def quick_preview(document_id):
    """
    Gera preview rápido sem dados de exemplo (apenas estrutura).
    
    Args:
        document_id: ID do documento no Google Drive
        
    Query Parameters:
        layout: Layout do formulário (padrão: single_column)
        theme: Tema visual (padrão: default)
        
    Returns:
        JSON com preview básico
    """
    try:
        user_id = str(current_user.id)
        layout = request.args.get('layout', 'single_column')
        theme = request.args.get('theme', 'default')
        
        logger.info(f"Gerando preview rápido do formulário {document_id}")
        
        # Converte documento em template (usando cache se disponível)
        converted_template = template_converter.convert_document_to_template(
            user_id=user_id,
            document_id=document_id
        )
        
        # Gera preview sem dados de exemplo
        form_preview = preview_generator.generate_form_preview(
            template=converted_template,
            layout=layout,
            theme=theme,
            include_sample_data=False
        )
        
        # Remove dados desnecessários para preview rápido
        quick_preview_data = {
            'template_info': form_preview['template_info'],
            'form_structure': {
                'type': form_preview['form_structure']['type'],
                'sections': [
                    {
                        'id': section['id'],
                        'title': section['title'],
                        'field_count': len(section.get('fields', []))
                    }
                    for section in form_preview['form_structure']['sections']
                ]
            },
            'visual_config': {
                'theme_name': form_preview['visual_config']['theme_name'],
                'colors': form_preview['visual_config']['colors']
            },
            'preview_metadata': form_preview['preview_metadata']
        }
        
        return jsonify({
            'success': True,
            'quick_preview': quick_preview_data,
            'message': f'Preview rápido gerado: {len(converted_template.fields)} campos'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no preview rápido: {e}")
        return jsonify({
            'success': False,
            'error': 'quick_preview_error',
            'message': 'Erro na geração de preview rápido'
        }), 500


@preview_generation_bp.route('/compare', methods=['POST'])
@limiter.limit("3 per minute")
@login_required
def compare_previews():
    """
    Compara diferentes layouts/temas para o mesmo documento.
    
    Request Body:
        {
            "document_id": "ID_do_documento",
            "template_name": "Nome (opcional)",
            "template_category": "Categoria (opcional)",
            "comparisons": [
                {"layout": "single_column", "theme": "default"},
                {"layout": "two_column", "theme": "modern"},
                {"layout": "grouped", "theme": "compact"}
            ]
        }
        
    Returns:
        JSON com comparação de previews
    """
    try:
        data = request.get_json() or {}
        document_id = data.get('document_id')
        template_name = data.get('template_name')
        template_category = data.get('template_category')
        comparisons = data.get('comparisons', [])
        
        if not document_id:
            return jsonify({
                'success': False,
                'error': 'missing_document_id',
                'message': 'document_id é obrigatório'
            }), 400
        
        if not comparisons or len(comparisons) > 5:
            return jsonify({
                'success': False,
                'error': 'invalid_comparisons',
                'message': 'comparisons deve ter entre 1 e 5 configurações'
            }), 400
        
        user_id = str(current_user.id)
        
        logger.info(f"Comparando {len(comparisons)} previews para documento {document_id}")
        
        # Converte documento em template uma vez
        converted_template = template_converter.convert_document_to_template(
            user_id=user_id,
            document_id=document_id,
            template_name=template_name,
            template_category=template_category
        )
        
        # Gera previews para cada configuração
        preview_results = []
        
        for i, config in enumerate(comparisons):
            layout = config.get('layout', 'single_column')
            theme = config.get('theme', 'default')
            
            try:
                form_preview = preview_generator.generate_form_preview(
                    template=converted_template,
                    layout=layout,
                    theme=theme,
                    include_sample_data=False  # Sem dados de exemplo na comparação
                )
                
                preview_results.append({
                    'config_index': i,
                    'layout': layout,
                    'theme': theme,
                    'preview': form_preview,
                    'success': True
                })
                
            except Exception as e:
                logger.warning(f"Erro na configuração {i} (layout: {layout}, theme: {theme}): {e}")
                preview_results.append({
                    'config_index': i,
                    'layout': layout,
                    'theme': theme,
                    'error': str(e),
                    'success': False
                })
        
        # Análise comparativa
        successful_previews = [p for p in preview_results if p['success']]
        comparison_analysis = {
            'total_configs': len(comparisons),
            'successful_configs': len(successful_previews),
            'template_info': {
                'id': converted_template.template_id,
                'name': converted_template.name,
                'field_count': len(converted_template.fields)
            },
            'recommendations': self._generate_layout_recommendations(successful_previews)
        }
        
        return jsonify({
            'success': True,
            'comparison_results': preview_results,
            'analysis': comparison_analysis,
            'message': f'Comparação concluída: {len(successful_previews)}/{len(comparisons)} previews gerados'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na comparação de previews: {e}")
        return jsonify({
            'success': False,
            'error': 'comparison_error',
            'message': 'Erro na comparação de previews'
        }), 500


@preview_generation_bp.route('/export/<document_id>', methods=['POST'])
@limiter.limit("2 per minute")
@login_required
def export_preview():
    """
    Exporta preview em diferentes formatos (JSON, HTML, etc.).
    
    Args:
        document_id: ID do documento
        
    Request Body:
        {
            "format": "json|html|vue|react",
            "layout": "single_column",
            "theme": "default",
            "include_sample_data": true,
            "template_name": "Nome (opcional)",
            "template_category": "Categoria (opcional)"
        }
        
    Returns:
        Preview exportado no formato solicitado
    """
    try:
        data = request.get_json() or {}
        export_format = data.get('format', 'json')
        layout = data.get('layout', 'single_column')
        theme = data.get('theme', 'default')
        include_sample_data = data.get('include_sample_data', True)
        template_name = data.get('template_name')
        template_category = data.get('template_category')
        
        valid_formats = ['json', 'html', 'vue', 'react']
        if export_format not in valid_formats:
            return jsonify({
                'success': False,
                'error': 'invalid_format',
                'message': f'Formato deve ser um de: {", ".join(valid_formats)}'
            }), 400
        
        user_id = str(current_user.id)
        
        logger.info(f"Exportando preview do documento {document_id} em formato {export_format}")
        
        # Converte documento em template
        converted_template = template_converter.convert_document_to_template(
            user_id=user_id,
            document_id=document_id,
            template_name=template_name,
            template_category=template_category
        )
        
        # Gera preview
        form_preview = preview_generator.generate_form_preview(
            template=converted_template,
            layout=layout,
            theme=theme,
            include_sample_data=include_sample_data
        )
        
        # Exporta no formato solicitado
        if export_format == 'json':
            exported_content = form_preview
            content_type = 'application/json'
        elif export_format == 'html':
            exported_content = self._export_to_html(form_preview)
            content_type = 'text/html'
        elif export_format == 'vue':
            exported_content = self._export_to_vue(form_preview)
            content_type = 'text/plain'
        elif export_format == 'react':
            exported_content = self._export_to_react(form_preview)
            content_type = 'text/plain'
        
        return jsonify({
            'success': True,
            'export': {
                'format': export_format,
                'content': exported_content,
                'content_type': content_type,
                'filename': f"{converted_template.name.lower().replace(' ', '_')}_preview.{export_format}",
                'size': len(str(exported_content))
            },
            'template_info': {
                'id': converted_template.template_id,
                'name': converted_template.name,
                'field_count': len(converted_template.fields)
            },
            'message': f'Preview exportado em formato {export_format.upper()}'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na exportação de preview: {e}")
        return jsonify({
            'success': False,
            'error': 'export_error',
            'message': 'Erro na exportação de preview'
        }), 500


def _generate_layout_recommendations(successful_previews: List[Dict]) -> List[str]:
    """Gera recomendações baseadas nos previews bem-sucedidos."""
    recommendations = []
    
    if len(successful_previews) < 2:
        recommendations.append("Teste mais configurações para comparação melhor")
        return recommendations
    
    # Análise de complexidade
    field_counts = []
    for preview in successful_previews:
        field_count = preview['preview']['template_info']['field_count']
        field_counts.append(field_count)
    
    avg_fields = sum(field_counts) / len(field_counts)
    
    if avg_fields <= 5:
        recommendations.append("Para formulários simples, layout 'single_column' é recomendado")
    elif avg_fields <= 15:
        recommendations.append("Para formulários médios, considere 'two_column' ou 'grouped'")
    else:
        recommendations.append("Para formulários complexos, use 'wizard' para melhor UX")
    
    # Análise de temas
    themes_used = {p['theme'] for p in successful_previews}
    if 'modern' in themes_used:
        recommendations.append("Tema 'modern' oferece melhor experiência visual")
    
    return recommendations


def _export_to_html(preview: Dict[str, Any]) -> str:
    """Exporta preview para HTML estático."""
    html_template = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{preview['template_info']['name']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .form-container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .form-field {{ margin-bottom: 1rem; }}
        .form-label {{ display: block; margin-bottom: 0.5rem; font-weight: 500; }}
        .form-input {{ width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; }}
        .required {{ color: red; }}
    </style>
</head>
<body>
    <div class="form-container">
        <h1>{preview['template_info']['name']}</h1>
        <p>{preview['template_info']['description']}</p>
        <form>
"""
    
    # Adiciona campos
    for section in preview['form_structure']['sections']:
        html_template += f"<fieldset><legend>{section['title']}</legend>"
        for field in section['fields']:
            required_mark = "<span class='required'>*</span>" if field['required'] else ""
            html_template += f"""
            <div class="form-field">
                <label class="form-label" for="{field['name']}">{field['label']}{required_mark}</label>
                <input class="form-input" type="text" id="{field['name']}" name="{field['name']}" placeholder="{field['props']['placeholder']}">
            </div>
            """
        html_template += "</fieldset>"
    
    html_template += """
        </form>
    </div>
</body>
</html>
"""
    return html_template


def _export_to_vue(preview: Dict[str, Any]) -> str:
    """Exporta preview para componente Vue.js."""
    return f"""
<template>
  <div class="form-container">
    <h1>{preview['template_info']['name']}</h1>
    <p>{preview['template_info']['description']}</p>
    <!-- Vue.js form implementation here -->
    <div v-for="section in formSections" :key="section.id">
      <h3>{{{{ section.title }}}}</h3>
      <div v-for="field in section.fields" :key="field.name" class="form-field">
        <label>{{{{ field.label }}}}</label>
        <input v-model="formData[field.name]" :type="field.type" :placeholder="field.props.placeholder">
      </div>
    </div>
  </div>
</template>

<script>
export default {{
  name: 'GeneratedForm',
  data() {{
    return {{
      formData: {{}},
      formSections: {preview['form_structure']['sections']}
    }}
  }}
}}
</script>
"""


def _export_to_react(preview: Dict[str, Any]) -> str:
    """Exporta preview para componente React."""
    return f"""
import React, {{ useState }} from 'react';

const GeneratedForm = () => {{
  const [formData, setFormData] = useState({{}});
  
  const formSections = {preview['form_structure']['sections']};
  
  return (
    <div className="form-container">
      <h1>{preview['template_info']['name']}</h1>
      <p>{preview['template_info']['description']}</p>
      {{formSections.map(section => (
        <div key={{section.id}}>
          <h3>{{section.title}}</h3>
          {{section.fields.map(field => (
            <div key={{field.name}} className="form-field">
              <label>{{field.label}}</label>
              <input
                type={{field.type}}
                placeholder={{field.props.placeholder}}
                value={{formData[field.name] || ''}}
                onChange={{e => setFormData({{...formData, [field.name]: e.target.value}})}}
              />
            </div>
          ))}}
        </div>
      ))}}
    </div>
  );
}};

export default GeneratedForm;
"""