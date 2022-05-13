from serial import *
import logging
from time import sleep
import serial
from scripts.settings import *
from scripts.crc import * 

def serialConnect(port, baudrate):
    #logMsgHead = "serial {}".format(s)
    """Подключение к сериал порту.  
    
    При неудачном соединении срабатывает exception и через
    каждые 1 сек попытка подключения повторяется бесконечно.

    """

    while True:
        try:
            s = serial.Serial(port=port, baudrate=baudrate, timeout=0.0001)
            #logger.debug("{}".format(s) + f'Connected')
            return s
        except SerialException as e:
            #logger.warning(f'{e} Will try to reconnect serial port')
            sleep(1)

def serialSendSimple(s, msg):
    """Отправляет данные по сериал порту без изменений."""
    logMsgHead = "serial {}".format(s)
    try:
        s.write(msg)
        print(msg)
    except SerialException as e:
        #logger.error(logMsgHead + f'{e}')
        s.close()  # Закрыть старый порт
        s = Serial()  # Создать новый порт
        #serialConnect(s)  # Попытаться подключиться к новому порту

def serialSendProtocol(s, master_slave: int, id: int, devType: int, cmd: int, buf):
    """Отправляет данные по сериал порту по протоколу.

    Особенности некоторых входных аргументов:  
    master_slave -- master -> 0xaa, slave -> 0xbb  
    id -- Число длиной не более 16-бит  
    buf -- Массив данных, минимальный массив: [0]  

    """
    logMsgHead = "serial {}".format(s)
    idH = (id & 0xff00) >> 8
    idL = id & 0xff

    msg = bytearray()
    bufLen = len(buf) + 5
    packSize = 10
    packQnt = int(bufLen / packSize) if bufLen % packSize == 0 else int((bufLen / packSize) + 1)

    msg.append(master_slave)
    msg.append(packQnt)
    msg.append(idH)
    msg.append(idL)
    msg.append(devType)
    msg.append(cmd)
    for b in buf: msg.append(b)

    # Заполняет остаток массива нулями для соответствия размеру пакетов.
    zeroQnt = packQnt * packSize - (len(msg) + 1)
    for i in range(zeroQnt): msg.append(0)
    
    msg.append(crc.getCrc8(msg))

    try:
        s.write(msg)
        print('send')
        print(msg)
    except SerialException as e:
        #logger.error(logMsgHead + f'{e}')
        s.close()  # Закрыть старый порт
        s = Serial()  # Создать новый порт
        s.serialConnect()  # Попытаться подключиться к новому порту


def serial_recv_simple(s, length):
    #Принимает данные по сериал порту заданной длины с таймаутом
    logMsgHead = "serial {}".format(s)
    msg = None

    try:
        msg = s.read(length)
    except SerialException as e:
        #logger.error(logMsgHead + f'{e}.')
        s.close()
        s = Serial()
        #serialConnect(s)
    else:
        s.reset_input_buffer()
    
    return msg
    
def serialRecvProtocol(s, master_slave: int, timeout: float):
    """Принимает данные по сериал порту.

    Особенности некоторых входных аргументов:  
    master_slave -- Тип ожидаемого устройства: master -> 0xaa, slave -> 0xbb  
    timeout -- Таймаут на начало приема данных в сек. Значение <None>
    блокирует скрипт на приеме до прихода данных.  

    """
    logMsgHead = "serial {}".format(s)
    msg = None
    s.timeout = timeout
    try:
        firstPartData = s.read(2)
        print(list(firstPartData))
        if len(firstPartData) == 2:
            if firstPartData[0] == master_slave:
                secondPartDataLen = firstPartData[1] * 10 - 2
                secondPartData = s.read(secondPartDataLen)
                
                test_msg = firstPartData + secondPartData
                
                if test_msg[-1] == getCrc8(test_msg[:-1]):
                    msg = test_msg

    except SerialException as e:
        #logger.error(logMsgHead + f'{e}')
        s.close()  # Закрыть старый порт
        s = Serial()  # Создать новый порт
        #serialConnect(s)  # Попытаться подключиться к новому порту
    else:
        s.reset_input_buffer()

    return msg
