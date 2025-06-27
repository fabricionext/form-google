import google.generativeai as genai
import os

# Configura sua chave de API.
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

print("Modelos Gemini disponíveis:")
try:
    # Itera sobre todos os modelos disponíveis
    for m in genai.list_models():
        # Filtra apenas os modelos do tipo "GenerativeModel" que suportam 'generateContent'
        if "generateContent" in m.supported_generation_methods:
            print(f"- {m.name} (suporta generateContent)")
except Exception as e:
    print(f"Ocorreu um erro ao listar os modelos: {e}")
    print("Verifique se sua GOOGLE_API_KEY está configurada corretamente e é válida.")