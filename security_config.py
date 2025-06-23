"""
Configurações de segurança para a aplicação Flask.
"""

import os
from datetime import timedelta


def get_security_config():
    """Retorna as configurações de segurança."""
    return {
        # Chave secreta para sessões
        "SECRET_KEY": os.getenv("FLASK_SECRET_KEY", os.urandom(32).hex()),
        # Configurações de sessão
        "PERMANENT_SESSION_LIFETIME": timedelta(minutes=30),
        "SESSION_COOKIE_SECURE": True,  # Apenas HTTPS
        "SESSION_COOKIE_HTTPONLY": True,  # Acesso apenas via HTTP (não JavaScript)
        "SESSION_COOKIE_SAMESITE": "Lax",  # Proteção CSRF
        # Proteção CSRF
        "WTF_CSRF_ENABLED": True,
        "WTF_CSRF_TIME_LIMIT": 3600,  # 1 hora
        # Proteção contra ataques de força bruta
        "MAX_LOGIN_ATTEMPTS": 5,
        "LOCKOUT_TIME": 300,  # 5 minutos em segundos
        # Configurações de senha
        "PASSWORD_MIN_LENGTH": 12,
        "PASSWORD_COMPLEXITY": {
            "min_uppercase": 1,
            "min_lowercase": 1,
            "min_digits": 1,
            "min_special": 1,
        },
        # CORS
        "CORS_ORIGINS": [
            "https://appform.estevaoalmeida.com.br",
            "https://www.appform.estevaoalmeida.com.br",
        ],
        # Headers de segurança
        "SECURITY_HEADERS": {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' https: data:; connect-src 'self' https:;",
        },
        # Configurações de rate limiting
        "RATELIMIT_DEFAULT": "200 per day;50 per hour;10 per minute",
        "RATELIMIT_STORAGE_URL": "memory://",
        # Configurações de log
        "SECURITY_LOGIN_LOG": True,
        "SECURITY_LOGOUT_LOG": True,
        "SECURITY_USERNAME_ENABLED": False,
        "SECURITY_SEND_REGISTER_EMAIL": False,
        "SECURITY_RECOVERABLE": True,
        "SECURITY_TRACKABLE": True,
        "SECURITY_CHANGEABLE": True,
        # Configurações de e-mail (se aplicável)
        "MAIL_SERVER": os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        "MAIL_PORT": int(os.getenv("MAIL_PORT", 587)),
        "MAIL_USE_TLS": os.getenv("MAIL_USE_TLS", "true").lower() == "true",
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME", ""),
        "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD", ""),
        "MAIL_DEFAULT_SENDER": os.getenv(
            "MAIL_DEFAULT_SENDER", "no-reply@appform.estevaoalmeida.com.br"
        ),
    }
