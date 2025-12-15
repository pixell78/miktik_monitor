#!/bin/bash

PROCESS_NAME="mikrotik_dash_c.py"
COMMAND="/root/scripts/mikrotik_dash_c.py"

# Verifica se o processo está em execução
if ! pgrep -f "$PROCESS_NAME" > /dev/null; then
  echo "$(date): Processo não encontrado, iniciando..." >> /var/log/monitor_process.log
  nohup $COMMAND > /dev/null 2>&1 &
else
  echo "$(date): Processo está ativo." >> /var/log/monitor_process.log
fi
