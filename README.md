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
##  - Retrieves logs from MikroTik and stores them in InfluxDB over     ##
##    Telegraph for real time data.                                     ##
##  - Retention policies implemented to manage log data growth.         ##
##                                                                      ##
############################ LICENSE ####################################
##                GNU General Public License                            ##
##########################################################################

## NEED ##
# GRAFANA #
# TELEGRAPH #
# INFLUXDB #
# PYTHON #
