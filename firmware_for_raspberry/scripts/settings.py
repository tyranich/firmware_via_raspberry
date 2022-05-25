# This Python file uses the following encoding: utf-8
#import logging
from enum import Enum
from datetime import datetime
import logging, glob 
import logging.handlers
import os



### - Main Settings ---------------------------------------------- ###

SERIAL_PORT_1 = 'COM16'
# SERIAL_PORT = '/dev/ttyUSB0'
SERIAL_BAUDRATE_1 = 57600


TCP_SERVER_HOST = 'localhost' 
TCP_PORT = 112

MASTER_ID = 1

ANCHORS = [1]
ANCHORS_1 = [2]
ANCHORS_2 = [3]
ANCHORS_3 = [4]
ALL_ANCHORS = [1,2,3,4,5,6,7]

TAGS_QUANTITY = 6  # Количество меток в посылке от анкера (важно для парсинга)
POLL_DELAY = 0.1  # Задержка между опросами анкеров в сек (float)
#TIMEOUT = 0.002# Таймаут на прием данных по RS485 в сек
TIMEOUT = 0.005
MSG_LENGTH_TX_TCP = 64 
MSG_LENGTH_RX_TCP = 32

MSG_LENGTH_TX_SER = 32
MSG_LENGTH_RX_SER = 64

### - Enums ------------------------------------------------------ ###

class Preamble(Enum):
    master = 0xaa
    slave = 0xbb

class Command(Enum):
    preset = 1
    calibrate = 2
    characteristic = 3
    tagInfo = 4
    giveData = 5
    bootOut = 0xb5
    last_command = 0xb1
    lock_timer_main = 0xb2
    clear_flash = 0xb3
    write_in_flash = 0xb4
    start_main = 0xb5
    allow_run_programm = 0xb7
    broadcast = 0xff

class DeviceType(Enum):
    tag = 0
    anchor = 1
    master = 2
    cell = 3
    tagStorage = 4
    rollerStand = 5
    server = 6
 

class status_fimware(Enum):
    receive_command_main = 0xe0
    need_command_stop_timer = 0xe1
    need_command_clear_flash = 0xe2
    need_data = 0xe3
    cant_write_boot = 0xe4
    cant_write_flash = 0xe5
    cant_start_main = 0xe6
    unknown_command = 0xec



### - Logger Settings -------------------------------------------- ###

"""
Уровни логирования:
    - DEBUG
    - INFO
    - WARNING
    - ERROR
"""
directory = os.getcwd()

ERROR_LOG_FILENAME = "{}\\logs\\error-logs.log".format(directory)
WARNING_LOG_FILENAME = "{}\\logs\\warning-logs.log".format(directory)
FIRMWARE_MAIN_LOG_FILENAME = "{}\\logs\\firmware-main-logs.log".format(directory)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "%(asctime)s:%(name)s:%(process)d:%(lineno)d" "%(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }, 
        "simple": {
            "format": "%(asctime)s:%(name)s:%(message)s:%(lineno)d",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "error_formater": {
            "formatter": "default",
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": ERROR_LOG_FILENAME,
            "backupCount": 2,
        },
        
        "warning_formater": {
            "formatter": "simple",
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename":WARNING_LOG_FILENAME, 
            "backupCount": 2,
        },

        "firmware_main_formater":{
            "formatter": "simple",
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename":FIRMWARE_MAIN_LOG_FILENAME, 
            "maxBytes": 50,
            "backupCount": 1,
        }     
    },
    "loggers": {
        "main_firmware": { 
            "level": "DEBUG",
            "handlers": ["firmware_main_formater"],
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["error_formater", "warning_formater"]
    },
}

### -------------------------------------------------------------- ###