# Sistema de Backup e Restauração

Este documento detalha o funcionamento do sistema de backup automático e os procedimentos para restauração de dados.

## Visão Geral

- **Frequência**: Diária (2h da manhã)
- **Local**: `/var/backups/appform/`
- **Retenção Local**: 7 dias
- **Sincronização Remota**: Google Drive (pasta `appform_backups`)
- **Retenção Remota**: 30 dias
- **Monitoramento**: Logs em `/var/log/appform_backup.log` e `/var/log/appform_backup_gdrive.log`

### O que é salvo

- **Banco de Dados PostgreSQL**: Dump completo do banco de dados.
- **Arquivos do Aplicativo**: Todo o código-fonte (exceto arquivos temporários e de ambiente).
- **Configurações**: Arquivos de configuração do Nginx, systemd e `.env`.
- **Logs**: Logs da aplicação e do sistema.

### Estrutura de Arquivos

Os arquivos de backup e os scripts de gerenciamento estão localizados em:

```
/var/backups/appform/
├── appform_backup_*.tar.gz    # Backups compactados
└── scripts/
    ├── backup_appform.sh       # Script principal de backup
    ├── restore_appform.sh      # Script de restauração
    └── sync_backup_gdrive.sh   # Sincronização com Google Drive
```

## Procedimentos

### Executar um Backup Manual

Para executar um backup fora do horário agendado:

```bash
sudo /var/backups/appform/scripts/backup_appform.sh
```

### Restaurar a partir de um Backup

Para restaurar o sistema a partir de um arquivo de backup específico:

```bash
sudo /var/backups/appform/scripts/restore_appform.sh /caminho/para/backup.tar.gz
```

### Sincronizar com Google Drive Manualmente

Para forçar a sincronização dos backups locais com o Google Drive:

```bash
sudo /var/backups/appform/scripts/sync_backup_gdrive.sh
```

## Verificação e Solução de Problemas

### Verificar Logs

```bash
# Logs do backup local
sudo tail -f /var/log/appform_backup.log

# Logs da sincronização com Google Drive
sudo tail -f /var/log/appform_backup_gdrive.log
```

### Verificar Arquivos de Backup

1.  **Backups Locais**:
    ```bash
    sudo ls -lh /var/backups/appform/appform_backup_*.tar.gz
    ```

2.  **Backups no Google Drive**:
    - Acesse a pasta de backup no Google Drive e verifique se os arquivos mais recentes estão presentes.

### Solução de Problemas Comuns

- **Falha no backup**: Verifique os logs em `/var/log/appform_backup.log`.
- **Falha na sincronização**: Verifique os logs em `/var/log/appform_backup_gdrive.log`.
- **Espaço em disco insuficiente**: Limpe backups antigos manualmente, se necessário.
