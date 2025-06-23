"""
Middleware de segurança para a aplicação Flask.
"""

import time
from functools import wraps

from flask import g, jsonify, request
import os


class SecurityMiddleware:
    """Middleware para adicionar headers de segurança e proteções."""

    def __init__(self, app=None):
        """Inicializa o middleware."""
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Configura o middleware na aplicação."""
        # Adiciona os headers de segurança em todas as respostas
        app.after_request(self.add_security_headers)

        # Adiciona proteção contra ataques de força bruta
        self.rate_limits = {}
        app.before_request(self.rate_limit)

        # Adiciona proteção contra XSS e outros ataques
        app.before_request(self.security_checks)

    def add_security_headers(self, response):
        """Adiciona headers de segurança à resposta."""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "SAMEORIGIN",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; font-src 'self' https: data:; connect-src 'self' https:;",
        }

        # Adiciona os headers à resposta
        for header, value in security_headers.items():
            if header not in response.headers:
                response.headers[header] = value

        return response

    def rate_limit(self):
        """Implementa rate limiting para prevenir abuso."""
        # Ignora para arquivos estáticos
        if request.path.startswith("/static/"):
            return None

        # Obtém o IP do cliente
        client_ip = request.remote_addr
        current_time = int(time.time())

        # Configurações de rate limiting
        window = 60  # 1 minuto
        max_requests = 100  # Máximo de requisições por minuto

        # Inicializa o contador para o IP, se necessário
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = {"count": 0, "window_start": current_time}

        # Reseta o contador se a janela de tempo expirou
        if current_time - self.rate_limits[client_ip]["window_start"] > window:
            self.rate_limits[client_ip] = {"count": 0, "window_start": current_time}

        # Incrementa o contador
        self.rate_limits[client_ip]["count"] += 1

        # Verifica se o limite foi excedido
        if self.rate_limits[client_ip]["count"] > max_requests:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Too many requests. Please try again later.",
                    }
                ),
                429,
            )

        return None

    def security_checks(self):
        """Executa verificações de segurança."""
        # Proteção contra XSS nos parâmetros
        for key, value in request.args.items():
            if isinstance(value, str) and any(
                char in value for char in ["<", ">", '"', "'", "&"]
            ):
                request.args = request.args.copy()
                request.args[key] = value.replace("<", "&lt;").replace(">", "&gt;")

        # Proteção contra SQL Injection
        if request.method in ["POST", "PUT", "DELETE"]:
            if request.is_json:
                data = request.get_json() or {}
                for key, value in data.items():
                    if isinstance(value, str) and any(
                        char in value for char in [";", "--", "/*", "*/"]
                    ):
                        return (
                            jsonify({"status": "error", "message": "Invalid input."}),
                            400,
                        )

        return None


def require_api_key(f):
    """Decorator para exigir chave de API."""

    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if api_key != os.getenv("API_KEY"):
            return jsonify({"status": "error", "message": "Invalid API key"}), 401
        return f(*args, **kwargs)

    return decorated
