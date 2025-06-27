import re
from typing import Dict, List, Optional, Tuple


def validate_cpf(cpf: str) -> Tuple[bool, str]:
    """
    Valida CPF usando o algoritmo oficial.
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    if not cpf:
        return False, "CPF é obrigatório"
    
    # Remove caracteres não numéricos
    cpf_digits = re.sub(r'\D', '', cpf)
    
    if len(cpf_digits) != 11:
        return False, "CPF deve ter 11 dígitos"
    
    # Verifica se todos os dígitos são iguais
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


def validate_cnpj(cnpj: str) -> Tuple[bool, str]:
    """
    Valida CNPJ usando o algoritmo oficial.
    
    Returns:
        Tuple[bool, str]: (é_válido, mensagem_erro)
    """
    if not cnpj:
        return False, "CNPJ é obrigatório"
    
    # Remove caracteres não numéricos
    cnpj_digits = re.sub(r'\D', '', cnpj)
    
    if len(cnpj_digits) != 14:
        return False, "CNPJ deve ter 14 dígitos"
    
    # Verifica se todos os dígitos são iguais
    if cnpj_digits == cnpj_digits[0] * 14:
        return False, "CNPJ inválido"
    
    # Sequência de multiplicadores para o primeiro DV
    mult1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cnpj_digits[i]) * mult1[i] for i in range(12))
    resto = soma % 11
    dv1 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj_digits[12]) != dv1:
        return False, "CNPJ inválido"
    
    # Sequência de multiplicadores para o segundo DV
    mult2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    # Calcula segundo dígito verificador
    soma = sum(int(cnpj_digits[i]) * mult2[i] for i in range(13))
    resto = soma % 11
    dv2 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj_digits[13]) != dv2:
        return False, "CNPJ inválido"
    
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """Valida formato de email."""
    if not email:
        return False, "Email é obrigatório"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Formato de email inválido"
    
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """Valida formato de telefone brasileiro."""
    if not phone:
        return True, ""  # Telefone não é obrigatório
    
    phone_digits = re.sub(r'\D', '', phone)
    
    if len(phone_digits) not in [10, 11]:
        return False, "Telefone deve ter 10 ou 11 dígitos"
    
    return True, ""


def validate_cep(cep: str) -> Tuple[bool, str]:
    """Valida formato de CEP."""
    if not cep:
        return True, ""  # CEP não é obrigatório
    
    cep_digits = re.sub(r'\D', '', cep)
    
    if len(cep_digits) != 8:
        return False, "CEP deve ter 8 dígitos"
    
    return True, ""


class FormValidator:
    """Classe principal para validação de formulários."""
    
    def __init__(self):
        self.errors: List[str] = []
    
    def validate_pessoa_fisica(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Valida dados de pessoa física.
        
        Returns:
            Tuple[bool, List[str]]: (é_válido, lista_de_erros)
        """
        self.errors = []
        
        # Campos obrigatórios
        required_fields = {
            'primeiroNome': 'Primeiro nome',
            'sobrenome': 'Sobrenome',
            'cpf': 'CPF',
            'email': 'Email'
        }
        
        for field, name in required_fields.items():
            if not data.get(field):
                self.errors.append(f"{name} é obrigatório")
        
        # Validações específicas
        if data.get('cpf'):
            valid, error = validate_cpf(data['cpf'])
            if not valid:
                self.errors.append(error)
        
        if data.get('email'):
            valid, error = validate_email(data['email'])
            if not valid:
                self.errors.append(error)
        
        if data.get('telefoneCelular'):
            valid, error = validate_phone(data['telefoneCelular'])
            if not valid:
                self.errors.append(f"Telefone celular: {error}")
        
        if data.get('outroTelefone'):
            valid, error = validate_phone(data['outroTelefone'])
            if not valid:
                self.errors.append(f"Outro telefone: {error}")
        
        if data.get('cep'):
            valid, error = validate_cep(data['cep'])
            if not valid:
                self.errors.append(error)
        
        return len(self.errors) == 0, self.errors
    
    def validate_pessoa_juridica(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Valida dados de pessoa jurídica.
        
        Returns:
            Tuple[bool, List[str]]: (é_válido, lista_de_erros)
        """
        self.errors = []
        
        # Campos obrigatórios
        required_fields = {
            'razaoSocial': 'Razão Social',
            'cnpj': 'CNPJ',
            'email': 'Email',
            'nomeRepresentanteLegal': 'Nome do Representante Legal',
            'cpfRepresentante': 'CPF do Representante'
        }
        
        for field, name in required_fields.items():
            if not data.get(field):
                self.errors.append(f"{name} é obrigatório")
        
        # Validações específicas
        if data.get('cnpj'):
            valid, error = validate_cnpj(data['cnpj'])
            if not valid:
                self.errors.append(error)
        
        if data.get('cpfRepresentante'):
            valid, error = validate_cpf(data['cpfRepresentante'])
            if not valid:
                self.errors.append(f"CPF do representante: {error}")
        
        if data.get('email'):
            valid, error = validate_email(data['email'])
            if not valid:
                self.errors.append(error)
        
        return len(self.errors) == 0, self.errors
    
    def validate_form_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Valida dados do formulário baseado no tipo de pessoa.
        
        Returns:
            Tuple[bool, List[str]]: (é_válido, lista_de_erros)
        """
        tipo_pessoa = data.get('tipoPessoa', '').lower()
        
        if tipo_pessoa == 'pf':
            return self.validate_pessoa_fisica(data.get('dadosCliente', {}))
        elif tipo_pessoa == 'pj':
            return self.validate_pessoa_juridica(data.get('dadosCliente', {}))
        else:
            return False, ["Tipo de pessoa inválido"] 