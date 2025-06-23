import re
import unicodedata

from app import create_app
from app.peticionador.models import PeticaoPlaceholder
from extensions import db


# Função para converter para snake_case, minúsculo e sem acentos
def to_snake_case(s):
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ASCII", "ignore").decode("ASCII")
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = s.lower()
    s = re.sub(r"_+", "_", s)
    s = s.strip("_")
    return s


def main():
    app = create_app()
    with app.app_context():
        placeholders = PeticaoPlaceholder.query.all()
        alterados = 0
        for ph in placeholders:
            original = ph.chave
            novo = to_snake_case(original)
            if original != novo:
                print(f"Alterando: '{original}' -> '{novo}'")
                ph.chave = novo
                alterados += 1
        if alterados:
            db.session.commit()
            print(f"{alterados} chaves atualizadas com sucesso!")
        else:
            print("Nenhuma chave precisava ser alterada.")


if __name__ == "__main__":
    main()
