import os
import re
from pathlib import Path

from bs4 import BeautifulSoup

# Diretórios onde estão os templates
TEMPLATE_DIRS = [
    "app/templates/peticionador",
    "templates/peticionador",
]

# Regex para snake_case
SNAKE_CASE = re.compile(r"^[a-z0-9_]+$")

# Função para normalizar nomes


def is_snake_case(name):
    return bool(SNAKE_CASE.match(name))


def check_template_fields(template_path):
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    soup = BeautifulSoup(content, "html.parser")
    problems = []
    for tag in soup.find_all(["input", "select", "textarea"]):
        name = tag.get("name")
        if name and not is_snake_case(name):
            problems.append((name, tag))
    return problems


def main():
    print("--- Validação de nomes de campos em templates de formulário ---")
    total_problems = 0
    for base in TEMPLATE_DIRS:
        base_path = Path(base)
        if not base_path.exists():
            continue
        for file in base_path.glob("formulario*.html"):
            problems = check_template_fields(file)
            if problems:
                print(f"\nArquivo: {file}")
                for name, tag in problems:
                    print(f'  - Campo com name="{name}" NÃO está em snake_case!')
                total_problems += len(problems)
    if total_problems == 0:
        print("\nTodos os campos de todos os formulários estão em snake_case!")
    else:
        print(f"\nTotal de problemas encontrados: {total_problems}")


if __name__ == "__main__":
    main()
