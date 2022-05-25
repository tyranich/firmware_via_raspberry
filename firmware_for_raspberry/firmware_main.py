from scripts.lib_firmware import *
from scripts.settings import *
from scripts.serialPort import * 
import time

TIMEOUT_SHORT = 0.01
TIMEOUT_LONG = 0.5

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("main_firmware")


time1 = time.perf_counter()
s_1 = serial.Serial(port="COM22", baudrate=SERIAL_BAUDRATE_1, timeout=0.0001)
for id_ach_0 in ALL_ANCHORS:
    boot_from_main(s_1, id_ach_0)

#захват анкеров 
current_id_anch = list(waiting_finish_command(s_1, Command.lock_timer_main.value, timeout=TIMEOUT_SHORT,  block=True, id=ALL_ANCHORS, ))
logger.debug("captured anchors {}".format(current_id_anch))

#очистка флеша 
current_id_anch = list(waiting_finish_command(s_1, Command.clear_flash.value, timeout=9,  block=False, id=current_id_anch, ))
logger.debug("cleared flash {}".format(current_id_anch))

#запись прошивки во флеш 
path = 'anchor.hex'
strings_for_write = get_list_to_write(path)
print(current_id_anch)
temp_id = 0
for _ in current_id_anch:
    c = [0]
    c[0] = _
    for _1 in strings_for_write:
        print(list(_1), type(_1))
        temp_id = waiting_finish_command(s_1, Command.write_in_flash.value, timeout=TIMEOUT_SHORT,  block=True, id=c, data=_1)
        if _ not in temp_id:
            current_id_anch.remove(_)    
            break
logger.debug("software downloaded {}".format(current_id_anch))

#установка флага разрешения запуска 
current_id_anch = list(waiting_finish_command(s_1, Command.allow_run_programm.value, timeout=TIMEOUT_LONG,  block=True, id=current_id_anch, ))
logger.debug("start allowed {}".format(current_id_anch))

#запуск программы 
current_id_anch = list(waiting_finish_command(s_1, Command.start_main.value, timeout=TIMEOUT_SHORT,  block=True, id=current_id_anch, ))
logger.debug("anchors started {}".format(current_id_anch))

time_end = time.perf_counter() - time1
