"""
Testes unitários para os services refatorados.
Valida que a refatoração mantém a funcionalidade original.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
from flask import Flask
from datetime import datetime

# Configurar paths para imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFormularioService(unittest.TestCase):
    """Testes para FormularioService"""
    
    def setUp(self):
        """Setup básico para testes"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.test_slug = "teste-formulario-cnh"
    
    @patch('app.peticionador.services.formulario_service.FormularioGerado')
    @patch('app.peticionador.services.formulario_service.current_app')
    def test_formulario_service_init(self, mock_current_app, mock_formulario_gerado):
        """Testa inicialização do FormularioService"""
        with self.app.app_context():
            mock_current_app.logger = Mock()
            
            # Importar aqui para evitar problemas de contexto
            from app.peticionador.services.formulario_service import FormularioService
            
            service = FormularioService(self.test_slug)
            assert service.slug == self.test_slug
            assert service._form_gerado is None
            assert service._modelo is None
            assert service._placeholders is None
    
    def test_organizacao_campos_categorias(self):
        """Testa se a organização de campos por categoria funciona corretamente"""
        with self.app.app_context():
            # Mock dos placeholders para teste
            mock_placeholders = [
                Mock(chave="autor_nome", ordem=1),
                Mock(chave="autor_1_endereco_logradouro", ordem=2),
                Mock(chave="orgao_transito_nome", ordem=3),
                Mock(chave="processo_numero", ordem=4),
            ]
            
            # Mock da função de categorização
            def mock_categorize(chave):
                if "autor" in chave and "endereco" in chave:
                    return "autor_endereco"
                elif "autor" in chave:
                    return "autor_dados"
                elif "orgao_transito" in chave:
                    return "autoridades"
                elif "processo" in chave:
                    return "processo"
                return "outros"
            
            with patch('app.peticionador.services.formulario_service.categorize_placeholder_key', mock_categorize):
                from app.peticionador.services.formulario_service import FormularioService
                
                service = FormularioService(self.test_slug)
                service._placeholders = mock_placeholders
                
                # Mock current_app.logger
                with patch('app.peticionador.services.formulario_service.current_app') as mock_app:
                    mock_app.logger = Mock()
                    
                    campo_grupos = service.agrupar_campos_por_categoria()
                    
                    # Verificações
                    assert "autores" in campo_grupos
                    assert "autoridades" in campo_grupos
                    assert "processo" in campo_grupos
                    assert len(campo_grupos["autoridades"]) == 1
                    assert campo_grupos["autoridades"][0] == "orgao_transito_nome"


class TestDocumentoService(unittest.TestCase):
    """Testes para DocumentoService"""
    
    def setUp(self):
        """Setup básico para testes"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
    
    def test_documento_service_init(self):
        """Testa inicialização do DocumentoService"""
        with self.app.app_context():
            from app.peticionador.services.documento_service import DocumentoService
            
            service = DocumentoService()
            assert service._google_service is None
    
    def test_generate_filename(self):
        """Testa geração de nome de arquivo"""
        with self.app.app_context():
            from app.peticionador.services.documento_service import DocumentoService
            
            service = DocumentoService()
            
            # Mock do modelo
            mock_modelo = Mock()
            mock_modelo.nome = "Suspensão CNH"
            
            # Mock dos replacements
            replacements = {
                "autor_nome": "João",
                "autor_sobrenome": "Silva"
            }
            
            # Mock da data atual
            with patch('app.peticionador.services.documento_service.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "25-06-2025"
                
                filename = service._generate_filename(mock_modelo, replacements)
                
                assert "25-06-2025" in filename
                assert "João Silva" in filename
                assert "Suspensão CNH" in filename
    
    @patch('app.peticionador.services.documento_service.current_app')
    def test_build_replacements(self, mock_current_app):
        """Testa construção do dicionário de substituições"""
        with self.app.app_context():
            mock_current_app.logger = Mock()
            
            from app.peticionador.services.documento_service import DocumentoService
            
            service = DocumentoService()
            
            # Mock dos placeholders
            mock_placeholders = [
                Mock(chave="autor_nome"),
                Mock(chave="autor_cpf"),
                Mock(chave="processo_numero")
            ]
            
            # Mock dos dados do formulário
            form_data = {
                "autor_nome": "João Silva",
                "autor_cpf": "123.456.789-00",
                "processo_numero": "12345"
            }
            
            with patch('app.peticionador.services.documento_service.google_services') as mock_google:
                mock_google.get_current_date_formatted.return_value = "25 de junho de 2025"
                
                replacements = service._build_replacements(form_data, mock_placeholders)
                
                assert replacements["autor_nome"] == "João Silva"
                assert replacements["autor_cpf"] == "123.456.789-00"
                assert replacements["processo_numero"] == "12345"
                assert "data_atual" in replacements


class TestIntegracaoServices(unittest.TestCase):
    """Testes de integração entre services"""
    
    def setUp(self):
        """Setup para testes de integração"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
    
    @patch('app.peticionador.services.formulario_service.FormularioGerado')
    @patch('app.peticionador.services.formulario_service.PeticaoModelo')
    @patch('app.peticionador.services.formulario_service.PeticaoPlaceholder')
    def test_fluxo_completo_mock(self, mock_placeholder, mock_modelo, mock_formulario):
        """Testa fluxo completo com mocks"""
        with self.app.app_context():
            # Setup dos mocks
            mock_form_gerado = Mock()
            mock_form_gerado.nome = "Teste Formulário"
            mock_form_gerado.modelo_id = 1
            
            mock_formulario.query.filter_by.return_value.first.return_value = mock_form_gerado
            
            mock_modelo_obj = Mock()
            mock_modelo_obj.id = 1
            mock_modelo_obj.nome = "Suspensão CNH"
            mock_modelo_obj.google_doc_id = "doc123"
            mock_modelo_obj.pasta_destino_id = "pasta123"
            
            mock_modelo.query.get_or_404.return_value = mock_modelo_obj
            
            mock_placeholder.query.filter_by.return_value.order_by.return_value.all.return_value = []
            
            with patch('app.peticionador.services.formulario_service.current_app') as mock_app:
                mock_app.logger = Mock()
                
                from app.peticionador.services.formulario_service import FormularioService
                from app.peticionador.services.documento_service import DocumentoService
                
                # Teste do FormularioService
                form_service = FormularioService("teste-slug")
                assert form_service.form_gerado.nome == "Teste Formulário"
                assert form_service.modelo.nome == "Suspensão CNH"
                
                # Teste do DocumentoService
                doc_service = DocumentoService()
                
                form_data = {"autor_nome": "João", "autor_sobrenome": "Silva"}
                placeholders = []
                
                # Mock dos métodos internos
                with patch.object(doc_service, '_build_replacements') as mock_build:
                    with patch.object(doc_service, '_generate_filename') as mock_filename:
                        with patch.object(doc_service, '_handle_duplicate_check') as mock_duplicate:
                            mock_build.return_value = {"autor_nome": "João"}
                            mock_filename.return_value = "teste-arquivo"
                            mock_duplicate.return_value = "teste-arquivo-final"
                            
                            # Verificar que os métodos são chamados corretamente
                            try:
                                doc_service.gerar_documento_dinamico(mock_modelo_obj, form_data, placeholders)
                            except AttributeError:
                                # Esperado devido aos mocks não completos
                                pass
                            
                            mock_build.assert_called_once()
                            mock_filename.assert_called_once()
                            mock_duplicate.assert_called_once()


def run_tests():
    """Executa todos os testes"""
    print("🧪 EXECUTANDO TESTES DOS SERVICES REFATORADOS")
    print("=" * 50)
    
    # Descobrir e executar testes
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ TODOS OS TESTES PASSARAM!")
        print("✅ Services estão funcionando corretamente")
        print("✅ Pronto para testes reais com a rota V2")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print(f"❌ Falhas: {len(result.failures)}")
        print(f"❌ Erros: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests() 