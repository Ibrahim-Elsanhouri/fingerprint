#!/usr/bin/python3
# -*- coding: utf-8 -*-
import zk
from zk import const
from datetime import datetime
import configparser
import argparse
import requests
import atexit
import logging
import _thread
import time
import csv


parser = argparse.ArgumentParser(description='ZK Basic Reading Tests')
parser.add_argument('-c', '--config',
                    help='ZK Listening Service Configuration', default='zk.conf')
args = parser.parse_args()


# Read and parse config file
ConfParser = configparser.ConfigParser()
ConfParser.read(args.config)
address = ConfParser.get("config", "device_address")
port = int(ConfParser.get("config", "device_port"))
password = ConfParser.get("config", "password")
force_udp = ConfParser.get("config", "force_udp")
timeout = int(ConfParser.get("config", "conn_timeout"))
log_file = ConfParser.get("config", "log_file")
data_directory = ConfParser.get("config", "data_directory")
device_timezone = ConfParser.get("config", "device_timezone")
attendance_server_url = ConfParser.get("config", "attendance_server_url")
attendance_server_key = ConfParser.get("config", "attendance_server_key")
attendance_to_process_file = data_directory + 'attendance_log_to_process.csv'

# Configure the log file
logging.basicConfig(filename=log_file,
                    format='%(asctime)s | %(levelname)s | %(message)s',
                    level=logging.INFO)

# Construct the zk object in order to start connection
zk = zk.ZK(address, port=port, timeout=timeout,
           password=password, force_udp=force_udp, verbose=False)


# Monitor connection
def monitor_zk_device_connectivity():

    # Helper variable to monitor device connectivity
    device_connected = True
    while True:
        if zk.helper.test_ping():
            if device_connected == False:
                logging.warning("DEVICE WAS UNREACHABLE BUT IT IS NOW BACK")
                # Give the device time to boot up and get connected properly
                main_process()
                break
            device_connected = True
            logging.info("Pinging device at : {} | port : {} completed successfully.".format(
                address, port))
        else:
            device_connected = False
            logging.warning("Could not reach device at : {} | port : {}".format(
                address, port))
        time.sleep(10)


# Send attendance to the server
def send_attendance_to_server(attendances):
    copied_attendances = list(attendances)
    time.sleep(5)
    lastest_attendance_timestamp = ConfParser.get(
        "config", "lastest_attendance_timestamp")
    if len(copied_attendances) > 0:
        for attendance in copied_attendances:
            if attendance.timestamp > datetime.strptime(lastest_attendance_timestamp, '%Y/%m/%d %H:%M:%S'):
                data = {"params": {"attendance_server_key": attendance_server_key,
                                   "device_timezone": device_timezone,
                                   "attendance_log": [{"emp_id": attendance.user_id,
                                                       "att_timestamp": attendance.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                                       "operation": attendance.punch}]}}

                try:
                    response = requests.post(
                        attendance_server_url, json=data)
                    logging.info(response.json()['result']['msg'])
                    with open(attendance_to_process_file, mode='r') as attendance_file:
                        attendance_reader = csv.reader(
                            attendance_file, delimiter=',')
                        if len(list(attendance_reader)) > 0:
                            attendances_log = []
                            for attendance_row in attendance_reader:
                                attendances_log.append({"emp_id": attendance_row[0],
                                                        "att_timestamp": attendance_row[1],
                                                        "operation": attendance_row[2]})
                            data = {"params": {"attendance_server_key": attendance_server_key,
                                               "device_timezone": device_timezone,
                                               "attendance_log": attendances_log}}
                            response = requests.post(
                                attendance_server_url, json=data)
                            logging.info(response.json()[
                                'result']['msg'])
                            attendance_file = open(
                                attendance_to_process_file, mode='w')
                            attendance_file.write('')
                            attendance_file.close()
                except Exception as e:
                    with open(attendance_to_process_file, mode='a') as attendance_file:
                        attendance_writer = csv.writer(
                            attendance_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        attendance_writer.writerow(
                            [attendance.user_id, attendance.timestamp, attendance.punch])
                        logging.error("Failed to send HTTP request to server at : {} ERROR: {}".format(
                            attendance_server_url, e))
        # Update latest attendance timestamp in config file
        lastest_attendance_timestamp = ConfParser.get(
            "config", "lastest_attendance_timestamp")
        if copied_attendances[-1].timestamp > datetime.strptime(lastest_attendance_timestamp, '%Y/%m/%d %H:%M:%S'):
            ConfParser.set('config', 'lastest_attendance_timestamp',
                           copied_attendances[-1].timestamp.strftime("%Y/%m/%d %H:%M:%S"))
        config_file = open(args.config, mode='w')
        ConfParser.write(config_file)
        config_file.close()


logging.info("Service Started")


def main_process():
    # Helper variable for monitoring device connectivity
    connect = False
    lastest_attendance_timestamp = ConfParser.get(
        "config", "lastest_attendance_timestamp")
    while not connect:
        try:
            logging.info("Trying to connect to device at : {} | port : {}".format(
                address, port))
            zk.connect()
            logging.info("Connected Successfully to device at : {} | port : {}".format(
                address, port))
            connect = True
            attendances = zk.get_attendance()
            _thread.start_new_thread(
                send_attendance_to_server, (attendances,))
            try:
                _thread.start_new_thread(monitor_zk_device_connectivity, ())
            except:
                logging.warning(
                    "Unable to monitor device connectin exiting...")
                exit()

            for attendance in zk.live_capture():
                if attendance is not None:
                    data = {"params": {"attendance_server_key": attendance_server_key,
                                       "device_timezone": device_timezone,
                                       "attendance_log": [{"emp_id": attendance.user_id,
                                                           "att_timestamp": attendance.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                                           "operation": attendance.punch}]}}

                    # Update latest attendance timestamp in config file
                    ConfParser.set('config', 'lastest_attendance_timestamp',
                                   attendance.timestamp.strftime("%Y/%m/%d %H:%M:%S"))
                    config_file = open(args.config, mode='w')
                    ConfParser.write(config_file)
                    config_file.close()
                    try:
                        response = requests.post(
                            attendance_server_url, json=data)
                        logging.info(response.json()['result']['msg'])
                        with open(attendance_to_process_file, mode='r') as attendance_file:
                            attendance_reader = csv.reader(
                                attendance_file, delimiter=',')

                            attendances_log = []
                            for attendance_row in attendance_reader:
                                attendances_log.append({"emp_id": attendance_row[0],
                                                        "att_timestamp": attendance_row[1],
                                                        "operation": attendance_row[2]})
                            if len(attendances_log) > 0:
                                data = {"params": {"attendance_server_key": attendance_server_key,
                                                   "attendance_log": attendances_log}}
                                response = requests.post(
                                    attendance_server_url, json=data)
                                logging.info(response.json()['result']['msg'])
                                attendance_file = open(
                                    attendance_to_process_file, mode='w')
                                attendance_file.write('')
                                attendance_file.close()
                    except Exception as e:
                        with open(attendance_to_process_file, mode='a') as attendance_file:
                            attendance_writer = csv.writer(
                                attendance_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                            attendance_writer.writerow(
                                [attendance.user_id, attendance.timestamp, attendance.punch])
                        logging.error("Failed to send HTTP request to server at : {} ERROR: {}".format(
                            attendance_server_url, e))

                    logging.info("User {} Performed Operation {} at {} (Device's Time)".format(
                        attendance.user_id,
                        attendance.punch,
                        attendance.timestamp))

        except Exception as e:
            logging.warning("Failed to connect to device at : {} | port : {} ERROR : {}".format(
                address, port, e))
            time.sleep(5)


def exit_handler():
    logging.info("Service Stopped")


main_process()

atexit.register(exit_handler)
