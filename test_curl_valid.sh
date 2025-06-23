#!/bin/bash

echo "🧪 Testando geração de documentos com dados válidos..."

# Dados de teste com formato válido
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
      "dataNascimento": "1990-01-01",
      "cpf": "12345678901",
      "rg": "123456789",
      "estadoEmissorRG": "PA",
      "cnh": "12345678901",
      "cep": "86020020",
      "logradouro": "Praça Jardim de Alessandra",
      "numero": "123",
      "complemento": "Apto 1",
      "bairro": "Canadá",
      "cidade": "Londrina",
      "estado": "PR",
      "email": "teste@teste.com.br",
      "telefoneCelular": "11987654321",
      "outroTelefone": "",
      "endereco": "Praça Jardim de Alessandra, 123, Apto 1"
    }
  }' \
  -w "\n\n📊 Status Code: %{http_code}\n📊 Tempo Total: %{time_total}s\n" \
  -s

echo "✅ Teste concluído!" 