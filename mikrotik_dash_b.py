#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
##########################################################################
### This script is developed by TerminalX Soluções em código aberto    ###
### Date 17/06/2024 at 20:10                                           ### 
### modified 28/06/2024 at 21:00                                       ###
### BETA VERSION 1.2                                                  ###
##########################################################################
############################ ABOUT #######################################
##                  ADDRESS LIST EXTRACTOR:                             ##
##                                                                      ##
##  THIS SCRIPT USES AN API TO CONNECT TO A ROUTERBOARD ON THE          ##
##  ROUTEROS SYSTEM TO MONITOR ADDRESS LISTS, CONNECTIONS AND FIREWALL  ##
##  RULES                                                               ##
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
##    deleted from the MikroTik address list.                           ##
##                                                                      ##
############################ LICENSE ####################################
##                GNU General Public License                            ##
##########################################################################

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from librouteros import connect
from influxdb import InfluxDBClient
import time
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações do MikroTik
router = {
    'host': '192.168.x.y',  # IP do RB
    'username': 'admin',   # Usuário do RB
    'password': 'xxxxxxxx',  # Senha do RB
    'port': 8728  # Porta de API habilitada
}

# Função para conectar ao MikroTik
def connect_mikrotik():
    try:
        return connect(
            host=router['host'],
            username=router['username'],
            password=router['password'],
            port=router['port']
        )
    except Exception as e:
        logger.error(f"Erro ao conectar ao MikroTik: {e}")
        return None

api = connect_mikrotik()

# Extrair listas de endereços
def get_address_lists():
    try:
        result = api('/ip/firewall/address-list/print')
        logger.info("Dados obtidos do MikroTik.")
        return list(result)
    except Exception as e:
        logger.error(f"Erro ao obter dados do MikroTik: {e}")
        return []

# Extrair conexões ativas
def get_active_connections():
    try:
        result = api('/ip/firewall/connection/print')
        logger.info("Conexões ativas obtidas do MikroTik.")
        return list(result)
    except Exception as e:
        logger.error(f"Erro ao obter conexões ativas do MikroTik: {e}")
        return []

# Configurações do InfluxDB
influxdb_client = InfluxDBClient(
    host='localhost',
    port=8086,
    username='mikrotik_user',
    password='LoguserSenai2020#',
    database='mikrotik'
)

# Verifica a conexão com o InfluxDB
try:
    influxdb_client.ping()
    logger.info("Conexão com o InfluxDB estabelecida com sucesso.")
except Exception as e:
    logger.error(f"Erro ao conectar ao InfluxDB: {e}")
    exit(1)

# Verificar se um registro existe no InfluxDB
def is_entry_exists(address):
    query = f'SELECT * FROM address_list WHERE address = \'{address}\' ORDER BY time DESC LIMIT 1'
    result = influxdb_client.query(query)
    return list(result)

# Verificar se uma conexão existe no InfluxDB
def is_connection_exists(entry):
    src_address = entry.get('src-address')
    dst_address = entry.get('dst-address')
    protocol = entry.get('protocol')
    query = f'SELECT * FROM connections WHERE "src-address" = \'{src_address}\' AND "dst-address" = \'{dst_address}\' AND protocol = \'{protocol}\' ORDER BY time DESC LIMIT 1'
    result = influxdb_client.query(query)
    return list(result)

# Enviar dados para o InfluxDB
def send_to_influxdb(data, measurement):
    points = []
    increment = 0
    for entry in data:
        if measurement == "address_list" and not is_entry_exists(entry.get('address')):
            increment += 1
            point = {
                "measurement": measurement,
                "tags": {
                    "list": entry.get('list'),
                    "address": entry.get('address', ''),
                    "comment": entry.get('comment', '')
                },
                "fields": {
                    #"list": entry.get('list'),
                    "timeout": entry.get('timeout'),
                    "count": increment
                },
                "time": int(time.time() * 1000000000)
            }
            points.append(point)
            logger.info(f"Ponto adicionado: {point}")
        elif measurement == "connections" and not is_connection_exists(entry):
            increment += 1
            point = {
                "measurement": measurement,
                "tags": {
                    "src-address": entry.get('src-address', ''),
                    "dst-address": entry.get('dst-address', ''),
                    "protocol": entry.get('protocol', ''),
                    "state": entry.get('state', '')
                },
                "fields": {
                    "timeout": entry.get('timeout'),
                    "count": increment
                },
                "time": int(time.time() * 1000000000)
            }
            points.append(point)
            logger.info(f"Ponto adicionado: {point}")

    if points:
        try:
            influxdb_client.write_points(points)
            logger.info(f"{len(points)} pontos enviados para o InfluxDB.")
        except Exception as e:
            logger.error(f"Erro ao enviar pontos para o InfluxDB: {e}")
    else:
        logger.info("Nenhum ponto a enviar para o InfluxDB.")

# Verificar e remover entradas obsoletas
def check_and_remove_obsolete_entries(current_entries, measurement):
    try:
        result = influxdb_client.query(f'SELECT * FROM {measurement}')
        influxdb_entries = list(result.get_points())
        
        if measurement == "address_list":
            current_addresses = [entry.get('address') for entry in current_entries]
            for influx_entry in influxdb_entries:
                address_influx = influx_entry.get('address')
                if address_influx not in current_addresses:
                    logger.info(f"Removendo entrada obsoleta do InfluxDB: {address_influx}")
                    influxdb_client.query(f'DELETE FROM {measurement} WHERE address=\'{address_influx}\'')
        elif measurement == "connections":
            current_connections = {(entry.get('src-address'), entry.get('dst-address'), entry.get('protocol')) for entry in current_entries}
            for influx_entry in influxdb_entries:
                src_address_influx = influx_entry.get('src-address')
                dst_address_influx = influx_entry.get('dst-address')
                protocol_influx = influx_entry.get('protocol')
                if (src_address_influx, dst_address_influx, protocol_influx) not in current_connections:
                    logger.info(f"Removendo entrada obsoleta do InfluxDB: {src_address_influx} -> {dst_address_influx} [{protocol_influx}]")
                    influxdb_client.query(f'DELETE FROM {measurement} WHERE "src-address"=\'{src_address_influx}\' AND "dst-address"=\'{dst_address_influx}\' AND protocol=\'{protocol_influx}\'')
    
    except Exception as e:
        logger.error(f"Erro ao verificar e remover entradas obsoletas do InfluxDB: {e}")

# Loop para reenviar dados
while True:
    if api is None:
        api = connect_mikrotik()
    
    if api is not None:
        address_lists = get_address_lists()
        active_connections = get_active_connections()
        send_to_influxdb(address_lists, "address_list")
        send_to_influxdb(active_connections, "connections")
        check_and_remove_obsolete_entries(address_lists, "address_list")
        check_and_remove_obsolete_entries(active_connections, "connections")
    
    time.sleep(60)
