#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
##########################################################################
### This script is developed by TerminalX Soluções em código aberto    ###
### Date 17/06/2024 at 20:10                                           ### 
### modified 24/06/2024 at 00:59                                       ###
##########################################################################
############################ ABOUT #######################################
##                  ADDRESS LIST EXTRACTOR:                             ##
##                                                                      ##
##  THIS SCRIPT USES AN API TO CONNECT TO A ROUTERBOARD ON THE          ##
##  ROUTEROS SYSTEM TO MONITOR ADDRESS LISTS AND FIREWALL RULES,        ##
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

from librouteros import connect
from influxdb import InfluxDBClient
import time

# Configurações do MikroTik
router = {
    'host': '192.168.x.y',  # IP do RB
    'username': 'admin',   # Usuário do RB
    'password': 'xxxxxxxx',  # Senha do RB
    'port': 8728  # Porta de API habilitada
}

# MikroTik connect
try:
    api = connect(
        host=router['host'],
        username=router['username'],
        password=router['password'],
        port=router['port']
    )
    print("Conexão com o MikroTik estabelecida com sucesso.")
except Exception as e:
    print(f"Erro ao conectar ao MikroTik: {e}")
    exit(1)

# Extrair listas de endereços
def get_address_lists():
    try:
        result = api('/ip/firewall/address-list/print')
        print("Dados obtidos do MikroTik.")
        return list(result)  # Converter o gerador em uma lista
    except Exception as e:
        print(f"Erro ao obter dados do MikroTik: {e}")
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
    print("Conexão com o InfluxDB estabelecida com sucesso.")
except Exception as e:
    print(f"Erro ao conectar ao InfluxDB: {e}")
    exit(1)

# Verificar se um registro existe no InfluxDB
def is_entry_exists(address):
    query = f'SELECT * FROM address_list WHERE address = \'{address}\' ORDER BY time DESC LIMIT 1'
    result = influxdb_client.query(query)
    return list(result)

# Enviar dados para o InfluxDB
def send_to_influxdb(data):
    points = []
    increment = 0
    for entry in data:
        if not is_entry_exists(entry.get('address')):
            increment += 1
            point = {
                "measurement": "address_list",
                "tags": {
                    "list": entry.get('list'),
                    "address": entry.get('address', ''),
                    "comment": entry.get('comment', '')
                },
                "fields": {
                    "timeout": entry.get('timeout'),
                    "count": increment
                },
                "time": int(time.time() * 1000000000)
            }
            points.append(point)
            print(f"Ponto adicionado: {point}")
        else:
            print(f"Registro já existente para o endereço: {entry.get('address')}")

    if points:
        try:
            influxdb_client.write_points(points)
            print(f"{len(points)} pontos enviados para o InfluxDB.")
            
            result = influxdb_client.query('SELECT * FROM "address_list" LIMIT 5')
            print(f"Dados armazenados no InfluxDB: {list(result.get_points())}")
            
        except Exception as e:
            print(f"Erro ao enviar pontos para o InfluxDB: {e}")
    else:
        print("Nenhum ponto a enviar para o InfluxDB.")

# Verificar e remover entradas obsoletas
def check_and_remove_obsolete_entries(current_entries):
    try:
        result = influxdb_client.query('SELECT * FROM address_list')
        influxdb_entries = list(result.get_points())
        
        for influx_entry in influxdb_entries:
            address_influx = influx_entry.get('address')
            if address_influx not in [entry.get('address') for entry in current_entries]:
                print(f"Removendo entrada obsoleta do InfluxDB: {address_influx}")
                influxdb_client.query(f'DELETE FROM address_list WHERE address=\'{address_influx}\'')
    
    except Exception as e:
        print(f"Erro ao verificar e remover entradas obsoletas do InfluxDB: {e}")

# Loop para reenviar dados
while True:
    address_lists = get_address_lists()
    send_to_influxdb(address_lists)
    check_and_remove_obsolete_entries(address_lists)
    time.sleep(60)
