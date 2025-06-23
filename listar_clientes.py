#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import create_app
from app.models import Cliente

app = create_app()

with app.app_context():
    print("Clientes disponíveis:")
    clientes = Cliente.query.all()
    for c in clientes:
        print(f"ID: {c.id}, Nome: {c.primeiro_nome} {c.sobrenome}, CPF: {c.cpf}")
