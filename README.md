##########################################################################
### This script is developed by TerminalX Soluções em código aberto    ###
### Date 17/06/2024 at 20:10                                           ### 
### modified 07/07/2024 at 16:45                                       ###
### BETA VERSION 1.3                                                  ###
##########################################################################
############################ ABOUT #######################################
##                  ADDRESS LIST EXTRACTOR:                             ##
##                                                                      ##
##  THIS SCRIPT USES AN API TO CONNECT TO A ROUTERBOARD ON THE          ##
##  ROUTEROS SYSTEM TO MONITOR ADDRESS LISTS, CONNECTIONS, FIREWALL     ##
##  RULES AND LOGS                                                      ##
##  STORING THEM IN AN INFLUXDB DATABASE FOR PRESENTATION IN GRAFANA    ##
##  DASHBOARDS.                                                         ##
##                                                                      ##
##  THIS SCRIPT USES THE FOLLOWING LIBRARIES:                           ##
##      - LIBROUTEROS                                                   ##
##      - INFLUXDB                                                      ##
##                                                                      ##
########################### FEATURES ####################################
##  - Stores data in InfluxDB for real-time presentation of firewall    ##
##    status and connection conditions on Grafana dashboards.           ##
##  - Automatically removes entries from InfluxDB when they are         ##
##    deleted from the MikroTik address list, connections and logs.     ##
##  - Retrieves logs from MikroTik and stores them in InfluxDB.         ##
##  - Retention policies implemented to manage log data growth.         ##
##                                                                      ##
############################ LICENSE ####################################
##                GNU General Public License                            ##
##########################################################################

Instalação e Configuração do InfluxDB
Se ainda não instalou o InfluxDB, siga as instruções de instalação no site oficial do InfluxDB: https://www.influxdata.com/downloads/.
Após a instalação, crie a base de dados:
influx
No prompt do InfluxDB, execute:
CREATE DATABASE mikrotik;
CREATE USER mikrotik_user WITH PASSWORD 'mikrotik_password';
GRANT ALL ON mikrotik TO mikrotik_user;
Habilite a API e as portas no MikroTik:
/ip service enable api
/ip service set api port=8728
/ip firewall filter add chain=input protocol=tcp dst-port=8728 action=accept place-before=0
4. Instalação e Configuração do Telegraf
Para instalar o Telegraf em Debian Linux, execute os seguintes comandos como root:
# Adicionar a chave GPG do repositório do Telegraf
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
# Adicionar o repositório do Telegraf
source /etc/os-release
echo "deb https://repos.influxdata.com/${ID,,} ${VERSION_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
# Atualizar os repositórios e instalar o Telegraf
sudo apt-get update
sudo apt-get install telegraf
Edite o arquivo de configuração do Telegraf (/etc/telegraf/telegraf.conf) para incluir um input para executar o script Python:
[global_tags]
  environment = "production"

[[inputs.exec]]
  commands = ["python /root/scripts/mikrotik_address_list.py"]
  interval = "60s"
  timeout = "30s"
  data_format = "influx"

[[outputs.influxdb]]
  urls = ["http://localhost:8086"]
  database = "mikrotik"
  username = "mikrotik_user"
  password = "mikrotik_password"
  retention_policy = ""
  write_consistency = "any"
  timeout = "5s"

[agent]
  interval = "10s"
  round_interval = true
  metric_batch_size = 1000
  metric_buffer_limit = 10000
  collection_jitter = "0s"
  flush_interval = "10s"
  flush_jitter = "0s"
  precision = ""
  logfile = ""
  quiet = false
  hostname = ""
  omit_hostname = false

[[inputs.cpu]]
  percpu = true
  totalcpu = true
  collect_cpu_time = false
  report_active = false

[[inputs.mem]]
Reinicie o Telegraf:
systemctl restart telegraf
systemctl status telegraf
Verifique os logs do Telegraf:
journalctl -u telegraf -f
Verifique se os dados estão sendo recebidos no InfluxDB:
influx -username 'mikrotik_user' -password 'mikrotik_password'
USE mikrotik
SHOW MEASUREMENTS
Você deverá ver a medida address_list no InfluxDB.
5. Instalação e Configuração do Grafana
Para instalar e configurar o Grafana em um sistema Debian, execute os seguintes comandos como root:
sudo apt-get install -y software-properties-common wget
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana
Inicie e habilite o serviço do Grafana:
systemctl start grafana-server
systemctl enable grafana-server
Verifique o status do Grafana:
systemctl status grafana-server
Configuração Inicial do Grafana
    1. Acesse a interface web do Grafana em: http://<IP_DO_SEU_SERVIDOR>:3000.
    2. O login padrão é admin para usuário e senha.
    3. Você será solicitado a alterar a senha na primeira vez que fizer login.
Adicionar InfluxDB como Fonte de Dados no Grafana
    1. Após o login, vá para Configuration (ícone de engrenagem) > Data Sources.
    2. Clique em Add data source.
    3. Selecione InfluxDB.
    4. Configure a conexão com o InfluxDB:
        ◦ URL: http://localhost:8086
        ◦ Database: mikrotik
        ◦ User: mikrotik_user
        ◦ Password: mikrotik_password
Criar um Dashboard no Grafana
    1. Vá para Create (ícone de mais) > Dashboard.
    2. Adicione um novo painel (Add new panel).
    3. Configure a consulta para exibir os dados das listas de endereços:
        ◦ Na seção de consulta, use a seguinte consulta básica:
SELECT "comment" FROM "address_list" WHERE $timeFilter
        ◦ Ajuste a visualização conforme necessário (gráficos, tabelas, etc.).



   
