import re


def clean_document(doc):
    return re.sub(r"\D", "", str(doc or ""))


def is_cpf_valid(cpf):
    cpf = clean_document(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        check = ((value * 10) % 11) % 10
        if check != int(cpf[i]):
            return False
    return True


def is_cnpj_valid(cnpj):
    cnpj = clean_document(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calc(digits):
        sum_ = 0
        pos = len(digits) - 7
        for i in range(len(digits)):
            sum_ += int(digits[i]) * pos
            pos -= 1
            if pos < 2:
                pos = 9
        return sum_

    orig = cnpj[:12]
    dig1 = ((calc(orig) % 11) < 2) and 0 or (11 - (calc(orig) % 11))
    orig += str(dig1)
    dig2 = ((calc(orig) % 11) < 2) and 0 or (11 - (calc(orig) % 11))
    return cnpj[-2:] == f"{dig1}{dig2}"


def is_document_valid(doc):
    doc = clean_document(doc)
    if len(doc) == 11:
        return is_cpf_valid(doc)
    elif len(doc) == 14:
        return is_cnpj_valid(doc)
    return False


def capitalize_words(text):
    if not text:
        return ""
    preps = {"de", "da", "do", "dos", "das", "e", "a", "o", "em", "no", "na"}
    words = text.lower().split()
    return " ".join(
        w if i > 0 and w in preps else w.capitalize() for i, w in enumerate(words)
    )
