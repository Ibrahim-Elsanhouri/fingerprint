#!/bin/bash
################################################################################
# Script for installing ZKTeco service on Ubuntu 14.04, 15.04, 16.04 and 18.04 (could be used for other versions too)
# Author: Bashier Elbashier
#-------------------------------------------------------------------------------

if [ $# -eq 0 ]; then
  echo "SERVICE SUFFIX NOT PROVIDED, PROVIDE A NAME e. g. ./zkatt_install.sh device1"
  exit 1
fi

#################  ##        #  ###############   ##############          ##########     ############
#    ##      #           #          #                     ###             ##          ##
#      ##    #             #          #                   ##               ##            ##
#        ##  #               #          #                  ##               ##              ##
#          ####                #          ##############     ##               ##              ##
#            ##  #               #          #                  ##               ##              ##
#              ##    #             #          #                   ##               ##            ##
#                ##      #           #          #                    ###              ##          ##
#################  ##        #         #          ##############         ###########     ############    BY BASHIER ELBASHIER

OE_USER="zkatt"
OE_CONFIG="${OE_USER}-$1"
OE_HOME="/opt/${OE_CONFIG}"

#--------------------------------------------------
# Create System User zkatt
#--------------------------------------------------
echo -e "\n---- Create zkatt system user if he does not exist ----"
id -u $OE_USER &>/dev/null || adduser --system --quiet --shell=/bin/bash --gecos 'zkatt' --group $OE_USER &&

  #The user should also be added to the sudo'ers group.
  echo -e "\n---- Add ZKATT system user to the sudo'ers if he isn't already in it ----"
id -u $OE_USER &>/dev/null || adduser $OE_USER sudo

#--------------------------------------------------
# Create Log Directory
#--------------------------------------------------
echo -e "\n---- Create Log directory ----"
mkdir /var/log/$OE_CONFIG
chown $OE_USER:$OE_USER /var/log/$OE_CONFIG

#--------------------------------------------------
# Create Data Directories
#--------------------------------------------------
echo -e "\n---- Create Data directory ----"
mkdir $OE_HOME
mkdir ${OE_HOME}/.data
chown $OE_USER:$OE_USER $OE_HOME

#--------------------------------------------------
# Install ZKATT
#--------------------------------------------------
echo -e "\n==== Installing ZKATT Service ===="
cp -r zk zkatt.py ${OE_HOME}

# Fix file permissions
chown -R $OE_USER:$OE_USER ${OE_HOME}
chmod u+x ${OE_HOME}/zkatt.py

echo -e "* Creating service config file"
cat <<EOF >~/$OE_CONFIG
[config]
device_address = 192.168.8.199
device_port = 4370
password = 1234
force_udp = True
conn_timeout = 60
log_file = /var/log/$OE_CONFIG/zkatt.log
attendance_server_url = http://localhost:8069/biometric-attendance/add
attendance_server_key = 996654132
device_timezone = Africa/Cairo
data_directory = $OE_HOME/.data/
lastest_attendance_timestamp = 2021/01/01 00:00:00
EOF

echo -e "* Security Config File"
mv ~/$OE_CONFIG /etc/${OE_CONFIG}.conf
chown $OE_USER:$OE_USER /etc/${OE_CONFIG}.conf
chmod 640 /etc/${OE_CONFIG}.conf

#--------------------------------------------------
# Adding ZKATT as a deamon (initscript)
#--------------------------------------------------

echo -e "* Create init file"
cat <<EOF >~/$OE_CONFIG
#!/bin/sh
### BEGIN INIT INFO
# Provides: $OE_CONFIG
# Required-Start: \$remote_fs \$syslog
# Required-Stop: \$remote_fs \$syslog
# Should-Start: \$network
# Should-Stop: \$network
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: ZKTeco service
# Description: ZKTeco
### END INIT INFO
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/opt/zkatt
DAEMON=$OE_HOME/zkatt.py
NAME=$OE_CONFIG
DESC=$OE_CONFIG
# Specify the user name (Default: zkatt).
USER=$OE_USER
# Specify an alternate config file (Default: /etc/openerp-server.conf).
CONFIGFILE="/etc/${OE_CONFIG}.conf"
# pidfile
PIDFILE=/var/run/\${NAME}.pid
# Additional options that are passed to the Daemon.
DAEMON_OPTS="-c \$CONFIGFILE"
[ -x \$DAEMON ] || exit 0
[ -f \$CONFIGFILE ] || exit 0
checkpid() {
[ -f \$PIDFILE ] || return 1
pid=\`cat \$PIDFILE\`
[ -d /proc/\$pid ] && return 0
return 1
}
case "\${1}" in
start)
echo -n "Starting \${DESC}: "
start-stop-daemon --start --quiet --pidfile \$PIDFILE \
--chuid \$USER --background --make-pidfile \
--exec \$DAEMON -- \$DAEMON_OPTS
echo "\${NAME}."
;;
stop)
echo -n "Stopping \${DESC}: "
start-stop-daemon --stop --quiet --pidfile \$PIDFILE \
--oknodo
echo "\${NAME}."
;;
restart|force-reload)
echo -n "Restarting \${DESC}: "
start-stop-daemon --stop --quiet --pidfile \$PIDFILE \
--oknodo
sleep 1
start-stop-daemon --start --quiet --pidfile \$PIDFILE \
--chuid \$USER --background --make-pidfile \
--exec \$DAEMON -- \$DAEMON_OPTS
echo "\${NAME}."
;;
*)
N=/etc/init.d/\$NAME
echo "Usage: \$NAME {start|stop|restart|force-reload}" >&2
exit 1
;;
esac
exit 0
EOF

echo -e "* Security Init File"
mv ~/$OE_CONFIG /etc/init.d/$OE_CONFIG
chmod 755 /etc/init.d/$OE_CONFIG
chown root: /etc/init.d/$OE_CONFIG

echo -e "* Start ZKATT on Startup"
update-rc.d $OE_CONFIG defaults
