#!/bin/bash
################################################################################
# Script for uninstalling ZKTeco
# Author: Bashier Elbashier
#-------------------------------------------------------------------------------

if [ $# -eq 0 ]; then
    echo "SERVICE SUFFIX NOT PROVIDED, PROVIDE A NAME e. g. ./zkatt_uninstall.sh device1"
    exit 1
fi

if [ $1 == "purge" ]; then
    echo -e "\n---- Purging all zk services ----"
    echo -e "\n---- Stopping All ZKATT Services ----"
    service 'zkatt-*' stop
    echo -e "\n---- Removing all log files ----"
    rm -r /var/log/zkatt-*
    echo -e "\n---- Removing Configuration file ----"
    rm /etc/zkatt-*.conf
    echo -e "\n---- Removing data directory ----"
    rm -r /opt/zkatt-*
    echo -e "\n---- Removing daemon configuration ----"
    rm /etc/init.d/zkatt-*
    echo -e "\n---- Deleting service user ZKATT ----"
    userdel zkatt
    exit 1
fi

echo -e "\n---- Stopping Service ----"
service zkatt-$1 stop
echo -e "\n---- Removing log files ----"
rm -r /var/log/zkatt-$1
echo -e "\n---- Removing Configuration file ----"
rm /etc/zkatt-${1}.conf
echo -e "\n---- Removing data directory ----"
rm -r /opt/zkatt-$1
echo -e "\n---- Removing daemon configuration ----"
rm /etc/init.d/zkatt-$1
