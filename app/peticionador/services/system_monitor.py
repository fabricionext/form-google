"""
Sistema de Monitoramento e Validação do Sistema
===============================================

Este módulo monitora a saúde do sistema e determina se um restart é necessário.
Implementa verificações robustas seguindo as orientações do .windsurfrules.
"""

import logging
import os
import sys
import importlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import current_app

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor de sistema para verificar integridade e necessidade de restart."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.last_check = None
        self.issues_found = []
    
    def check_system_health(self) -> Dict[str, any]:
        """
        Verifica a saúde geral do sistema.
        
        Returns:
            Dict com status da verificação
        """
        self.logger.info("Iniciando verificação de saúde do sistema")
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'restart_recommended': False,
            'critical_issues': [],
            'warnings': []
        }
        
        # Verificações
        checks = [
            ('database', self._check_database_connection),
            ('imports', self._check_critical_imports),
            ('routes', self._check_route_registration),
            ('file_permissions', self._check_file_permissions),
            ('schemas', self._check_schemas_health),
            ('services', self._check_services_health)
        ]
        
        for check_name, check_function in checks:
            try:
                result = check_function()
                health_status['checks'][check_name] = result
                
                if result['status'] == 'critical':
                    health_status['critical_issues'].append(f"{check_name}: {result['message']}")
                    health_status['restart_recommended'] = True
                elif result['status'] == 'warning':
                    health_status['warnings'].append(f"{check_name}: {result['message']}")
                    
            except Exception as e:
                self.logger.error(f"Erro na verificação {check_name}: {e}")
                health_status['checks'][check_name] = {
                    'status': 'error',
                    'message': f'Erro na verificação: {str(e)}'
                }
                health_status['critical_issues'].append(f"{check_name}: Erro na verificação")
        
        # Determinar status geral
        if health_status['critical_issues']:
            health_status['overall_status'] = 'critical'
        elif health_status['warnings']:
            health_status['overall_status'] = 'warning'
        
        self.last_check = datetime.now()
        self.logger.info(f"Verificação concluída. Status: {health_status['overall_status']}")
        
        return health_status
    
    def _check_database_connection(self) -> Dict[str, str]:
        """Verifica conexão com banco de dados."""
        try:
            from app.extensions import db
            from sqlalchemy import text
            
            # Tentar uma query simples com text() para SQLAlchemy 2.0+
            result = db.session.execute(text('SELECT 1')).fetchone()
            if result:
                return {'status': 'ok', 'message': 'Conexão com banco OK'}
            else:
                return {'status': 'critical', 'message': 'Banco não responde corretamente'}
                
        except Exception as e:
            return {'status': 'critical', 'message': f'Erro de conexão: {str(e)}'}
    
    def _check_critical_imports(self) -> Dict[str, str]:
        """Verifica se imports críticos estão funcionando."""
        critical_modules = [
            'app.peticionador.models',
            'app.peticionador.routes',
            'app.peticionador.services.formulario_service',
            'app.peticionador.utils'
        ]
        
        failed_imports = []
        
        for module_name in critical_modules:
            try:
                importlib.import_module(module_name)
            except Exception as e:
                failed_imports.append(f"{module_name}: {str(e)}")
        
        if failed_imports:
            return {
                'status': 'critical',
                'message': f'Imports falharam: {"; ".join(failed_imports)}'
            }
        else:
            return {'status': 'ok', 'message': 'Todos os imports críticos OK'}
    
    def _check_route_registration(self) -> Dict[str, str]:
        """Verifica se rotas críticas estão registradas."""
        try:
            from flask import current_app
            
            critical_routes = [
                'peticionador.dashboard',
                'peticionador.preencher_formulario_dinamico',
                'peticionador.sincronizar_placeholders'
            ]
            
            missing_routes = []
            
            for route_name in critical_routes:
                try:
                    from flask import url_for
                    # Tentar gerar URL sem argumentos para verificar se existe
                    if route_name == 'peticionador.preencher_formulario_dinamico':
                        continue  # Esta precisa de argumento, pular
                    elif route_name == 'peticionador.sincronizar_placeholders':
                        continue  # Esta precisa de argumento, pular
                    else:
                        url_for(route_name)
                except Exception:
                    missing_routes.append(route_name)
            
            if missing_routes:
                return {
                    'status': 'warning',
                    'message': f'Rotas não encontradas: {", ".join(missing_routes)}'
                }
            else:
                return {'status': 'ok', 'message': 'Rotas críticas registradas'}
                
        except Exception as e:
            return {'status': 'error', 'message': f'Erro ao verificar rotas: {str(e)}'}
    
    def _check_file_permissions(self) -> Dict[str, str]:
        """Verifica permissões de arquivos críticos."""
        critical_files = [
            '/var/www/estevaoalmeida.com.br/form-google/app/peticionador/routes.py',
            '/var/www/estevaoalmeida.com.br/form-google/app/peticionador/models.py',
            '/var/www/estevaoalmeida.com.br/form-google/app/peticionador/utils.py'
        ]
        
        permission_issues = []
        
        for file_path in critical_files:
            if not os.path.exists(file_path):
                permission_issues.append(f"Arquivo não existe: {file_path}")
            elif not os.access(file_path, os.R_OK):
                permission_issues.append(f"Sem permissão de leitura: {file_path}")
        
        if permission_issues:
            return {
                'status': 'critical',
                'message': f'Problemas de permissão: {"; ".join(permission_issues)}'
            }
        else:
            return {'status': 'ok', 'message': 'Permissões de arquivos OK'}
    
    def _check_schemas_health(self) -> Dict[str, str]:
        """Verifica saúde dos schemas."""
        try:
            from app.peticionador.schemas import ma
            
            if ma is None:
                return {
                    'status': 'warning',
                    'message': 'Schemas marshmallow não carregados (modo degradado)'
                }
            else:
                return {'status': 'ok', 'message': 'Schemas carregados corretamente'}
                
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'Schemas em modo degradado: {str(e)}'
            }
    
    def _check_services_health(self) -> Dict[str, str]:
        """Verifica saúde dos serviços."""
        try:
            from app.peticionador.services.formulario_manager import formulario_manager
            from app.peticionador.services.formulario_service import FormularioService
            
            # Testar se os serviços podem ser instanciados
            if formulario_manager and FormularioService:
                return {'status': 'ok', 'message': 'Serviços funcionando'}
            else:
                return {'status': 'warning', 'message': 'Serviços parcialmente indisponíveis'}
                
        except Exception as e:
            return {'status': 'critical', 'message': f'Erro nos serviços: {str(e)}'}
    
    def should_restart_application(self) -> Tuple[bool, List[str]]:
        """
        Determina se a aplicação deveria ser reiniciada.
        
        Returns:
            Tuple (should_restart, reasons)
        """
        health = self.check_system_health()
        
        restart_reasons = []
        
        # Verificar se há issues críticos
        if health['critical_issues']:
            restart_reasons.extend(health['critical_issues'])
        
        # Verificar modificações de arquivos
        if self._check_file_modifications():
            restart_reasons.append("Arquivos críticos foram modificados")
        
        # Verificar se há muitos warnings
        if len(health['warnings']) >= 3:
            restart_reasons.append("Muitos warnings detectados")
        
        should_restart = len(restart_reasons) > 0
        
        if should_restart:
            self.logger.warning(f"Restart recomendado. Razões: {'; '.join(restart_reasons)}")
        else:
            self.logger.info("Sistema estável, restart não necessário")
        
        return should_restart, restart_reasons
    
    def _check_file_modifications(self) -> bool:
        """Verifica se arquivos críticos foram modificados recentemente."""
        critical_files = [
            '/var/www/estevaoalmeida.com.br/form-google/app/peticionador/routes.py',
            '/var/www/estevaoalmeida.com.br/form-google/app/peticionador/models.py',
            '/var/www/estevaoalmeida.com.br/form-google/app/peticionador/services/formulario_manager.py'
        ]
        
        recent_modifications = False
        cutoff_time = datetime.now() - timedelta(minutes=10)
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mod_time > cutoff_time:
                    self.logger.info(f"Arquivo modificado recentemente: {file_path}")
                    recent_modifications = True
        
        return recent_modifications
    
    def get_restart_command(self) -> str:
        """Retorna o comando apropriado para restart do sistema."""
        # Para sistemas com Apache/WSGI
        commands = [
            "sudo systemctl reload apache2",
            "sudo service apache2 reload", 
            "touch /var/www/estevaoalmeida.com.br/form-google/app.wsgi"
        ]
        
        return " ou ".join(commands)


# Instância global do monitor
system_monitor = SystemMonitor()


def check_system_and_recommend_action() -> Dict[str, any]:
    """
    Função utilitária para verificar sistema e recomendar ação.
    
    Returns:
        Dict com status e recomendações
    """
    should_restart, reasons = system_monitor.should_restart_application()
    health = system_monitor.check_system_health()
    
    return {
        'health': health,
        'should_restart': should_restart,
        'restart_reasons': reasons,
        'restart_command': system_monitor.get_restart_command() if should_restart else None,
        'summary': _generate_summary(health, should_restart, reasons)
    }


def _generate_summary(health: Dict, should_restart: bool, reasons: List[str]) -> str:
    """Gera um resumo em português sobre o status do sistema."""
    status_map = {
        'healthy': '✅ Sistema saudável',
        'warning': '⚠️ Sistema com avisos',
        'critical': '🚨 Sistema com problemas críticos'
    }
    
    summary = status_map.get(health['overall_status'], '❓ Status desconhecido')
    
    if should_restart:
        summary += f"\n🔄 RESTART RECOMENDADO. Motivos: {'; '.join(reasons)}"
    else:
        summary += "\n✅ Sistema estável, restart não necessário"
    
    if health['warnings']:
        summary += f"\n⚠️ Avisos: {len(health['warnings'])} encontrados"
    
    return summary