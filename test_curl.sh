#!/bin/bash

echo "🧪 Testando geração de documentos via curl..."

# Dados de teste fornecidos pelo usuário
curl -X POST "https://appform.estevaoalmeida.com.br/api/gerar-documento" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: test-key" \
  -d '{
    "tipoPessoa": "pf",
    "dadosCliente": {
      "tipoPessoa": "PF",
      "primeiroNome": "João",
      "sobrenome": "Teste",
      "nacionalidade": "Brasileiro(a)",
      "estadoCivil": "Divorciado(a)",
      "profissao": "Qualquer",
      "dataNascimento": "20000-01-01",
      "cpf": "000.000.000-00",
      "rg": "0000",
      "estadoEmissorRG": "PA",
      "cnh": "00000000000",
      "cep": "86020-020",
      "logradouro": "Praça Jardim de Alessandra",
      "numero": "00",
      "complemento": "0000",
      "bairro": "Canadá",
      "cidade": "Londrina",
      "estado": "PR",
      "email": "teste@teste.com.br",
      "telefoneCelular": "(99) 99999-9999",
      "outroTelefone": "",
      "endereco": "Praça Jardim de Alessandra, 00, 0000"
    }
  }' \
  -w "\n\n📊 Status Code: %{http_code}\n📊 Tempo Total: %{time_total}s\n" \
  -s

echo "✅ Teste concluído!" 