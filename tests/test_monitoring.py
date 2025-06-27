#!/usr/bin/env python3
"""
Script principal para testar o sistema de monitoramento (Grafana Loki)
"""
import os
import subprocess
import sys

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()


def check_dependencies():
    """Verifica se as dependências estão instaladas"""
    print("🔍 Verificando dependências...")

    try:
        import requests

        print("✅ requests instalado")
    except ImportError:
        print("❌ requests não encontrado")
        print("💡 Execute: pip install requests")
        return False

    return True


def check_monitoring_services():
    """Verifica se os serviços de monitoramento estão rodando"""
    print("\n🔧 Verificando serviços de monitoramento...")

    # Verificar se o Docker está rodando
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker está rodando")

            # Verificar se os containers estão rodando
            if "loki" in result.stdout and "grafana" in result.stdout:
                print("✅ Containers Loki e Grafana estão rodando")
                return True
            else:
                print("⚠️  Containers não encontrados")
                print("💡 Execute: ./start_monitoring.sh")
                return False
        else:
            print("❌ Docker não está rodando")
            return False
    except FileNotFoundError:
        print("❌ Docker não está instalado")
        return False


def run_loki_test():
    """Executa o teste do Grafana Loki"""
    print("\n🧪 Executando teste do Grafana Loki...")

    try:
        result = subprocess.run(
            [sys.executable, "test_loki.py"], capture_output=True, text=True
        )

        print(result.stdout)
        if result.stderr:
            print("⚠️  Avisos/Erros:")
            print(result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"❌ Erro ao executar teste do Grafana Loki: {e}")
        return False


def show_next_steps():
    """Mostra os próximos passos"""
    print("\n" + "=" * 60)
    print("🎉 TESTE DE MONITORAMENTO CONCLUÍDO!")
    print("=" * 60)

    print("\n📊 PRÓXIMOS PASSOS:")

    print("\n1. 📈 GRAFANA LOKI:")
    print("   - Acesse: http://localhost:3000")
    print("   - Login: admin / admin")
    print("   - Vá para 'Explore'")
    print("   - Selecione 'Loki' como fonte de dados")
    print('   - Use a query: {app="form-google"}')
    print("   - Você deve ver os logs de teste")

    print("\n2. 🛠️ CONFIGURAÇÃO EM PRODUÇÃO:")
    print("   - Ajuste as configurações de logging conforme necessário")
    print("   - Monitore regularmente os dashboards")
    print("   - Configure alertas se necessário")

    print("\n3. 📚 DOCUMENTAÇÃO:")
    print("   - README.md: Visão geral do sistema")
    print("   - MONITORING_SETUP.md: Configuração do Grafana Loki")


def main():
    """Função principal"""
    print("🚀 INICIANDO TESTE DO SISTEMA DE MONITORAMENTO")
    print("=" * 60)

    # Verificar dependências
    if not check_dependencies():
        print("\n❌ Dependências não atendidas. Instale as dependências primeiro.")
        return

    # Verificar serviços
    services_ok = check_monitoring_services()

    # Executar testes
    loki_ok = run_loki_test()

    # Resumo
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES:")
    print("=" * 60)
    print(f"✅ Dependências: {'OK' if check_dependencies() else 'FALHOU'}")
    print(f"🔧 Serviços: {'OK' if services_ok else 'FALHOU'}")
    print(f"📊 Grafana Loki: {'OK' if loki_ok else 'FALHOU'}")

    if loki_ok:
        show_next_steps()
    else:
        print("\n❌ Alguns testes falharam. Verifique as configurações.")


if __name__ == "__main__":
    main()
