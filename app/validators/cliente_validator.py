"""
Validador para dados do cliente com sanitização e validação robusta.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from flask import current_app

logger = logging.getLogger(__name__)


@dataclass
class ClienteData:
    """Dados do cliente validados"""

    tipo_pessoa: str
    primeiro_nome: str
    sobrenome: str
    email: str
    cpf: Optional[str] = None
    cnpj: Optional[str] = None
    rg: Optional[str] = None
    cnh: Optional[str] = None
    data_nascimento: Optional[str] = None
    telefone_celular: Optional[str] = None
    endereco_logradouro: Optional[str] = None
    endereco_numero: Optional[str] = None
    endereco_complemento: Optional[str] = None
    endereco_bairro: Optional[str] = None
    endereco_cidade: Optional[str] = None
    endereco_estado: Optional[str] = None
    endereco_cep: Optional[str] = None
    nacionalidade: Optional[str] = None
    estado_civil: Optional[str] = None
    profissao: Optional[str] = None
    estado_emissor_rg: Optional[str] = None


class ClienteValidator:
    """Validador para dados do cliente"""

    def __init__(self):
        self.erros = []

    def validar_dados(self, data: Dict[str, Any]) -> ClienteData:
        """
        Valida e sanitiza dados do cliente

        Args:
            data: Dicionário com dados do cliente

        Returns:
            ClienteData validado

        Raises:
            ValueError: Se os dados forem inválidos
        """
        self.erros = []

        # Sanitizar dados
        dados_sanitizados = self._sanitizar_dados(data)

        # Validar campos obrigatórios
        self._validar_campos_obrigatorios(dados_sanitizados)

        # Validar campos específicos
        self._validar_cpf_cnpj(dados_sanitizados)
        self._validar_email(dados_sanitizados)
        self._validar_cep(dados_sanitizados)
        self._validar_telefone(dados_sanitizados)
        self._validar_data_nascimento(dados_sanitizados)

        # Se há erros, levantar exceção
        if self.erros:
            raise ValueError(f"Dados inválidos: {'; '.join(self.erros)}")

        # Converter para ClienteData
        return ClienteData(**dados_sanitizados)

    def _sanitizar_dados(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza dados removendo caracteres perigosos e espaços extras"""
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Remove espaços extras
                value = " ".join(value.split())
                # Remove caracteres de controle
                value = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", value)
                # Remove caracteres perigosos para nomes de arquivo
                value = re.sub(r'[<>:"/\\|?*]', "", value)
                # Limita tamanho
                if len(value) > 200:
                    value = value[:200]

            sanitized[key] = value

        return sanitized

    def _validar_campos_obrigatorios(self, data: Dict[str, Any]):
        """Valida campos obrigatórios"""
        campos_obrigatorios = [
            ("tipoPessoa", "Tipo de pessoa"),
            ("primeiroNome", "Primeiro nome"),
            ("sobrenome", "Sobrenome"),
            ("email", "Email"),
        ]

        for campo, nome in campos_obrigatorios:
            valor = data.get(campo)
            if not valor or not str(valor).strip():
                self.erros.append(f"{nome} é obrigatório")

        # Validar tipo de pessoa
        tipo_pessoa = data.get("tipoPessoa")
        if tipo_pessoa and tipo_pessoa not in ["pf", "pj"]:
            self.erros.append("Tipo de pessoa deve ser 'pf' ou 'pj'")

    def _validar_cpf_cnpj(self, data: Dict[str, Any]):
        """Valida CPF ou CNPJ conforme tipo de pessoa"""
        tipo_pessoa = data.get("tipoPessoa")
        cpf = data.get("cpf")
        cnpj = data.get("cnpj")

        if tipo_pessoa == "pf":
            if cpf:
                # Remove caracteres não numéricos
                cpf_limpo = re.sub(r"\D", "", cpf)
                if len(cpf_limpo) != 11:
                    self.erros.append("CPF deve ter 11 dígitos")
                elif not self._validar_cpf_algoritmo(cpf_limpo):
                    self.erros.append("CPF inválido")

        elif tipo_pessoa == "pj":
            if cnpj:
                # Remove caracteres não numéricos
                cnpj_limpo = re.sub(r"\D", "", cnpj)
                if len(cnpj_limpo) != 14:
                    self.erros.append("CNPJ deve ter 14 dígitos")
                elif not self._validar_cnpj_algoritmo(cnpj_limpo):
                    self.erros.append("CNPJ inválido")

    def _validar_cpf_algoritmo(self, cpf: str) -> bool:
        """Valida CPF usando algoritmo oficial"""
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False

        # Validação do primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto

        if int(cpf[9]) != digito1:
            return False

        # Validação do segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto

        return int(cpf[10]) == digito2

    def _validar_cnpj_algoritmo(self, cnpj: str) -> bool:
        """Valida CNPJ usando algoritmo oficial"""
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False

        # Validação do primeiro dígito verificador
        multiplicadores1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * multiplicadores1[i] for i in range(12))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto

        if int(cnpj[12]) != digito1:
            return False

        # Validação do segundo dígito verificador
        multiplicadores2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * multiplicadores2[i] for i in range(13))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto

        return int(cnpj[13]) == digito2

    def _validar_email(self, data: Dict[str, Any]):
        """Valida formato do email"""
        email = data.get("email")
        if email:
            # Regex básica para email
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email):
                self.erros.append("Email inválido")

    def _validar_cep(self, data: Dict[str, Any]):
        """Valida formato do CEP"""
        cep = data.get("endereco_cep")
        if cep:
            # Remove caracteres não numéricos
            cep_limpo = re.sub(r"\D", "", cep)
            if len(cep_limpo) != 8:
                self.erros.append("CEP deve ter 8 dígitos")

    def _validar_telefone(self, data: Dict[str, Any]):
        """Valida formato do telefone"""
        telefone = data.get("telefone_celular")
        if telefone:
            # Remove caracteres não numéricos
            telefone_limpo = re.sub(r"\D", "", telefone)
            if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
                self.erros.append("Telefone deve ter 10 ou 11 dígitos")

    def _validar_data_nascimento(self, data: Dict[str, Any]):
        """Valida formato da data de nascimento"""
        data_nasc = data.get("data_nascimento")
        if data_nasc:
            # Aceita formatos: DD/MM/AAAA, AAAA-MM-DD, DD-MM-AAAA
            data_patterns = [
                r"^\d{2}/\d{2}/\d{4}$",
                r"^\d{4}-\d{2}-\d{2}$",
                r"^\d{2}-\d{2}-\d{4}$",
            ]

            if not any(re.match(pattern, data_nasc) for pattern in data_patterns):
                self.erros.append(
                    "Data de nascimento deve estar no formato DD/MM/AAAA, AAAA-MM-DD ou DD-MM-AAAA"
                )

    @staticmethod
    def validar_cpf(cpf: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Valida CPF com verificações de segurança.
        
        Args:
            cpf: String com CPF em qualquer formato
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
            (válido, cpf_limpo, mensagem_erro)
        """
        if not cpf:
            return False, None, "CPF não informado"
        
        # Remove caracteres não numéricos
        cpf_digits = re.sub(r"\D", "", cpf.strip())
        
        # Validação de tamanho
        if len(cpf_digits) > 11:
            current_app.logger.warning(f"CPF com tamanho inválido: {len(cpf_digits)} dígitos")
            return False, None, "CPF deve ter no máximo 11 dígitos"
        
        if len(cpf_digits) < 11:
            # Se for menor que 11, aceitar mas com warning
            current_app.logger.info(f"CPF parcial recebido: {cpf_digits}")
            
        # Validação de caracteres maliciosos
        if re.search(r'[<>"\';%\\]', cpf):
            current_app.logger.warning(f"CPF com caracteres suspeitos: {cpf}")
            return False, None, "Formato de CPF inválido"
        
        # Se chegou aqui, está válido para busca
        return True, cpf_digits, None
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Valida CNPJ com verificações de segurança.
        
        Args:
            cnpj: String com CNPJ em qualquer formato
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
            (válido, cnpj_limpo, mensagem_erro)
        """
        if not cnpj:
            return False, None, "CNPJ não informado"
        
        # Remove caracteres não numéricos
        cnpj_digits = re.sub(r"\D", "", cnpj.strip())
        
        # Validação de tamanho
        if len(cnpj_digits) > 14:
            current_app.logger.warning(f"CNPJ com tamanho inválido: {len(cnpj_digits)} dígitos")
            return False, None, "CNPJ deve ter no máximo 14 dígitos"
        
        # Validação de caracteres maliciosos
        if re.search(r'[<>"\';%\\]', cnpj):
            current_app.logger.warning(f"CNPJ com caracteres suspeitos: {cnpj}")
            return False, None, "Formato de CNPJ inválido"
        
        return True, cnpj_digits, None
    
    @staticmethod
    def validar_email(email: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Valida email com verificações de segurança.
        
        Args:
            email: String com email
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: 
            (válido, email_limpo, mensagem_erro)
        """
        if not email:
            return False, None, "Email não informado"
        
        email = email.strip().lower()
        
        # Validação de tamanho
        if len(email) > 320:  # RFC 5321
            return False, None, "Email muito longo"
        
        # Validação básica de formato
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, None, "Formato de email inválido"
        
        # Validação de caracteres maliciosos
        if re.search(r'[<>"\';%\\]', email):
            current_app.logger.warning(f"Email com caracteres suspeitos: {email}")
            return False, None, "Formato de email inválido"
        
        return True, email, None
    
    @staticmethod
    def sanitizar_string(texto: str, max_length: int = 255) -> str:
        """
        Sanitiza string removendo caracteres perigosos.
        
        Args:
            texto: String a ser sanitizada
            max_length: Tamanho máximo permitido
            
        Returns:
            String sanitizada
        """
        if not texto:
            return ""
        
        # Remove caracteres perigosos
        texto_limpo = re.sub(r'[<>"\';%\\]', '', texto.strip())
        
        # Trunca se necessário
        if len(texto_limpo) > max_length:
            texto_limpo = texto_limpo[:max_length]
            current_app.logger.warning(f"String truncada para {max_length} caracteres")
        
        return texto_limpo


def validar_dados_cliente(data: Dict[str, Any]) -> ClienteData:
    """
    Função conveniente para validar dados do cliente

    Args:
        data: Dicionário com dados do cliente

    Returns:
        ClienteData validado

    Raises:
        ValueError: Se os dados forem inválidos
    """
    validator = ClienteValidator()
    return validator.validar_dados(data)
