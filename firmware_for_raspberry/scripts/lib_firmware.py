import logging.config
import time
from scripts.serialPort import *
from scripts.crc import *
from scripts.settings import *
import sys
""" 
1. переписать отправку данных для прошивки
2. написать функцию вывода из бутлоадера с проверками
3. дописать логирование 
4. исправить ошибку логирования(запись сразу в 2 файла, должно писаться в один)
"""
TIMEOUT_WAIT_DEFAULT = 0.006 #Это посылка 20 байт и прием ответа 10 байт. На скорости 57600 это 5760 байт в секунду. 30/5760 = 6 миллисекунд. 
COUNTER_ATTEMPT = 30
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

def get_status_comm(message):
    return list(message)[6]


def get_last_comm(message):
    return list(message)[5]


def get_crc_last_comm(message):
    return list(message)[7]


def get_crc_mess(message):
    return list(message)[-1]


def get_id_mess(message):
    return list(message)[3]


def error_detection(recv_list, command):
    check_list = list(recv_list)
    if get_status_comm(check_list) == 0:
        logger.warning("Непонятно что происходит, отправлена команда {}".format(command))
    elif get_status_comm(check_list) == 1:
        print("команда {} начала выполнение".format(command))
        return 1
    elif get_status_comm(check_list) == 100:
        print("команда {} завершила выполнение".format(command))
        return 1
    elif get_status_comm(check_list) == 224:
        logger.warning("Ошибка команда бутлоодера попала в main {}".format(check_list))
        return -1
    elif get_status_comm(check_list) == 225:
        logger.error("Не сброшен таймер, остановите таймер {}".format(check_list))
        return -1
    elif get_status_comm(check_list) == 226:
        logger.error("Флеш не очищена {}".format(check_list))
        return -1
    elif get_status_comm(check_list) == 227:
        logger.warning("Мало данных, не соответствует 1му байту 9посылки {}".format(check_list))
        return -1
    elif get_status_comm(check_list) == 228: 
        logger.error("Запись в запрещенный сектор(область загрузчика или настроек) {}".format(check_list))
        return -1
    elif get_status_comm(check_list) == 229:
        logger.error("Не удалось записать данные во флеш {}".format(check_list))
        return -1
    elif get_status_comm(check_list) == 230:
        logger.warning("Нельзя запускать приложение, происходит загрузка данных {}".format(check_list))
        return -1
    elif get_status_comm(check_list) == 231:
        logger.warning("Низкий заряд аккумулятора {}".format(check_list))
        return -1
    elif get_status_comm(check_list) == 236:
        logger.warning("Получена неизвестная команда {}".format(check_list))
        return -1 
    else:
        print("Неизвестное условие, проверьте полученные данные {}".format(check_list))
        return -1


def deleted_id_from_dict(dict_, id):
    if dict_.get(id):
        dict_.pop(id)
    else:
        return


def boot_from_main(s, id):
    time.sleep(0.1) 
    cmdBootOut_1 = [0xAA, 0x01, 0x00, 0x00, 0x01, 0x04, 0x00, 0x00, 0x00]
    cmdBootOut_1[2] = (id >> 8) & 0xff
    cmdBootOut_1[3] =  id & 0xff
    cmdBootOut_1.append(getCrc8(cmdBootOut_1))
    print("Выведен в загрузчик {}".format(cmdBootOut_1[3]))
    serialSendSimple(s, cmdBootOut_1)


def check_sum(string, current_crc): #проверка контрольной суммы файла, указана в конце строки файла 
    string = string.decode('utf-8')
    #print(string)
    string_for_hex = string
    byte_string = bytes.fromhex(string_for_hex)
    return_chek_sum = 0
    for _ in byte_string:
        return_chek_sum += _
    return_chek_sum = 0xff & -return_chek_sum
    if return_chek_sum == current_crc:
        return True
    else:
        return False


def recv_dada_from_file(file, length_str): #получить следующую пачку данных из открытого файла 
    return file.read(length_str)


def get_list_to_write(path_file):
    LEN_STRING = 16
    NUM_SYS = 16
    
    read_string = None
    counter_crc = 0
    counter_string = 0
    i = 0 

    dict_string = {"start": None, "len_data": None, "flash_adress": None, "type_write": None, "data": None, "crc": None, "end_line": None}
    list_string_hex = []
    try:

        read_file = open(path_file, 'rb')
        while dict_string["type_write"] != b'05':
            read_string = recv_dada_from_file(read_file, 1)
            if read_string == b':':
                dict_string['start'] = read_string

                read_string = recv_dada_from_file(read_file, 2)
                dict_string['len_data'] = read_string
                
                read_string = recv_dada_from_file(read_file, 4)
                dict_string['flash_adress'] = read_string
                
                read_string = recv_dada_from_file(read_file, 2)
                dict_string['type_write'] = read_string
                
                #проверяем тип записи, если тип записи равен 04, \
                # то данные из строки означают первые 4 символа адреса флеша
                if dict_string['type_write'] == b'04': 
                    len_data_string = int(dict_string['len_data'].decode('utf-8'), NUM_SYS) 
                    read_string = recv_dada_from_file(read_file, len_data_string * 2)
                    dict_string['start_flash'] = read_string
                else:
                    len_data_string = int(dict_string['len_data'].decode('utf-8'), NUM_SYS) 
                    read_string = recv_dada_from_file(read_file, len_data_string * 2)
                    #если количество данных меньше 16, недостающее количество дополняем нулями 
                    if len_data_string < LEN_STRING: 
                        additional_data = b'00' * (LEN_STRING - len_data_string)
                        dict_string['data'] = read_string + additional_data
                    else:    
                        dict_string['data'] = read_string
                    
                read_string = recv_dada_from_file(read_file, 2)
                dict_string['crc'] = read_string
                
                read_string = recv_dada_from_file(read_file, 1)
                dict_string['end_line'] = read_string
                if dict_string['end_line'] == b'\r':
                    #если тип записи = b'00' - то складываем данные для посылки и помещаем в очередь
                    if dict_string["type_write"] == b'00': 
                        #проверка контрольной суммы строки 
                        crc_string = int(dict_string['crc'].decode('utf-8'), NUM_SYS)
                        string_for_check = dict_string['len_data'] + dict_string['flash_adress'] + dict_string['type_write'] + dict_string['data']
                        #проверка на равенство суммы успешных проверок и количества строк для записи
                        
                        if check_sum(string_for_check, crc_string):
                            counter_crc += 1
                        else:
                            #если хоть одна строка файла не прошла проверку контрольной суммы, закрываем программу и возвращаем False
                            read_file.close()
                            return False
                        
                        counter_string += 1

                        
                        string_for_write = dict_string['start_flash'] + dict_string['flash_adress'] + dict_string['data']
                        list_string_hex.append(bytes.fromhex(string_for_write.decode('utf-8')))
                    continue
            else:
                continue
        print(counter_crc, counter_string)
        read_file.close()
        return list_string_hex if counter_crc == counter_string else False
    
    except FileNotFoundError as Ex_Read_file:
            print(Ex_Read_file)#указанный в пути файл не найден, либо не верный путь 
            sys.exit()
            
    except Exception as ex:
        read_file.close()
        print(ex)




def compilance_check(id, command, dict_start, dict_completed, msg_recv, msg_send=None):
    """
    Функция проверки сообщения на соответсвие протоколу, так же записывет статусы команды 
    в соотвутсвующий словарь, если статус команды = 1  - started_commands, если статус команды = 100
    - comleted_commands. Значение команд смотрите в файле описания бутлоадера. Возвращает -1 в случае 
    получения статуса ошибки. 
    """
    if get_id_mess(msg_recv) == id and get_last_comm(msg_recv) == command:
        if command == Command.write_in_flash.value:
            if get_crc_last_comm(msg_recv) == get_crc_mess(msg_send):
                if get_status_comm(msg_recv) < 100:
                    dict_start[id] = 1
                elif get_status_comm(msg_recv) == 100:
                    dict_completed[id] = 100
                else:
                    return_status = error_detection(msg_recv, command)
                    return return_status
            else:
                return_status = -1
                return return_status
        else:
            if get_status_comm(msg_recv) < 100:
                dict_start[id] = 1
            elif get_status_comm(msg_recv) == 100:
                dict_completed[id] = 100
            else:
                return_status = error_detection(msg_recv, command)
                return return_status
    else:
        return None


def sorting_dict(dict1, dict2):
    sorted_dict = {x[0]:x[1] for x in dict1.items() if x[1] == 100}
    dict2.update(sorted_dict)
    for _ in sorted_dict.keys():
        if dict1.get(_):
            dict1.pop(_)


def create_msg_command(command, id, data = 0):
    msg = None
    send_comm_buff = [0xAA, 0x01, 0x00, 0x00, 0x20, 0xB5, 0x00, 0x00, 0x00]
    send_comm_buff[2] = (id >> 8) & 0xff
    send_comm_buff[3] =  id & 0xff
    send_comm_buff[5] = command
    if command == 0xb4:
        send_comm_buff = send_comm_buff[:9] + list(data)
        send_comm_buff[1] = (len(send_comm_buff) + 1) // 10
        crc = getCrc8(send_comm_buff) # высчитываем црц 
        send_comm_buff.append(crc) # доваляем црц к массиву  
    else:
        send_comm_buff.append(getCrc8(send_comm_buff))

    print(send_comm_buff)
    return(send_comm_buff)

    
def waiting_finish_command(s, command, timeout=float, block = bool, id=list, data=0):
    """
    s - дескриптор последовательного порта, comman - команда завершение которой мы ждем, 
    timeout - задержка между отправкой команды анкеру и попытки получить ответ от него, 
    block - режим функци, если True то ждет пока каждый анкер не выполнит коману, если False
    то рассылает всем и ждет выполнение асинхронно. id список анкеров, всегда list. 
    
    """
    completed_commands =  {}
    started_commands = {}
    if block:
        for id_anch in id:
            counter_cycle = 0
            while not started_commands.get(id_anch) and not completed_commands.get(id_anch): #проверка словарей готовности 
                send_command = create_msg_command(command, id_anch, data)
                serialSendSimple(s, send_command) # отправка команды 
                
                time.sleep(TIMEOUT_WAIT_DEFAULT)
                msg = serialRecvProtocol(s, Preamble.slave.value, TIMEOUT_WAIT_DEFAULT * 4) # получение команды 
                if msg:
                    print(list(msg))
                    if compilance_check(id_anch, command, started_commands, completed_commands, msg, msg_send=send_command) == -1: # проверка сообщения на соблюдение протокола бутлоадера
                        logger.error("Error anch {}".format(id_anch))
                        break
                else:
                    counter_cycle += 1
                    if counter_cycle % 2 == 0:
                        serialSendSimple(s, send_command) # отправка команды 
                    elif counter_cycle > COUNTER_ATTEMPT:
                        logger.error("started anchor {} didn`t answer 10 times {}".format(id_anch, command))
                        break 
            
            if id_anch in started_commands.keys(): #проверяем не был ли удален анкер из списка айдишников
                if not completed_commands.get(id_anch): #проверяем нет ли анкера в словаре завершенных команд
                    time.sleep(timeout)     
                    request_last_command = create_msg_command(Command.last_command.value, id_anch, data)

                while not completed_commands.get(id_anch): #оправшиваем анкер пока его айдишник не является ключом в словаре завершенных команд
                    serialSendSimple(s, request_last_command)
                    time.sleep(TIMEOUT_WAIT_DEFAULT)
                    msg = serialRecvProtocol(s, Preamble.slave.value, TIMEOUT_WAIT_DEFAULT * 4)
                    counter_cycle += 1
                    if msg:
                        print(list(msg))
                        if compilance_check(id_anch, command, started_commands, completed_commands, msg, msg_send=send_command) == -1:
                            logger.error("Error anch {}".format(list(msg)))
                            break
                    else:
                        serialSendSimple(s, request_last_command)
                        if counter_cycle > COUNTER_ATTEMPT:
                            logger.error("completed anchor {} didn`t answer 10 times {}".format(id_anch, command))
                            break
                    time.sleep(TIMEOUT_WAIT_DEFAULT)
            else:
                continue

        print(completed_commands, started_commands)
        return completed_commands


    if not block: 
        counter_failed_reads = {x:0 for x in id}
        for id_anch in id:
            send_command = create_msg_command(command, id_anch, data)
            print(started_commands, completed_commands)
            serialSendSimple(s, send_command)
            time.sleep(TIMEOUT_WAIT_DEFAULT)
            while not started_commands.get(id_anch):  
                msg = serialRecvProtocol(s, Preamble.slave.value, TIMEOUT_WAIT_DEFAULT * 4)
                if msg:
                    if compilance_check(id_anch, command, started_commands, completed_commands, msg) == -1:
                        logger.error("Error anch {}".format(list(msg)))
                        break
                else:
                    counter_failed_reads[id_anch] += 1
                    time.sleep(TIMEOUT_WAIT_DEFAULT)   
                    if counter_failed_reads[id_anch] % 2 == 0:
                        serialSendSimple(s, send_command)
                        time.sleep(TIMEOUT_WAIT_DEFAULT)
                    elif counter_failed_reads[id_anch] > COUNTER_ATTEMPT:
                        logger.error("started anchor {} didn`t answer 10 times {}".format(id_anch, command)) 
                        if command == Command.clear_flash.value:
                            started_commands[id_anch] = 0
                        break
        
        time.sleep(timeout)

        copy_started_commands = started_commands.copy() #создаем копию словаря, запущеных команд что бы не редактировать основной словарь
        print(completed_commands, started_commands)
        while len(completed_commands) < len(started_commands):          
            for id_anch2 in copy_started_commands.keys():
                request_last_command = create_msg_command(Command.last_command.value, id_anch2, data)
                serialSendSimple(s, request_last_command)
                time.sleep(TIMEOUT_WAIT_DEFAULT)
                msg = serialRecvProtocol(s, Preamble.slave.value, TIMEOUT_WAIT_DEFAULT * 4)

                if msg:
                    print(list(msg))
                    if compilance_check(id_anch2, command, started_commands, completed_commands, msg) == -1:
                        logger.error("Error anch {}".format(list(msg)))
                        break
                    
                else:
                    counter_failed_reads[id_anch] += 1
                    if counter_failed_reads[id_anch] > COUNTER_ATTEMPT: 
                        deleted_id_from_dict(copy_started_commands, id_anch)
                        deleted_id_from_dict(started_commands, id_anch)
                        logger.error("completed anchor {} didn`t answer 10 times {}".format(id_anch, command))
                        break

            for key_compl_comm in completed_commands.keys():
                deleted_id_from_dict(copy_started_commands, key_compl_comm)

        print(completed_commands, started_commands)
        print(counter_failed_reads)
        return completed_commands
    print(completed_commands, started_commands)
    return completed_commands
