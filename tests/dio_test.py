from time import sleep
import sys
sys.path.append('src')
from bs1200.driver import BS1200

box = 1
with BS1200([box]) as bs:
    bs.query_system_status(box)
    bs.config_can_publishing(box, True, True, True)
    ai_v = bs.readback_ai_all(box)
    print(bs.i_fmt_txt.format(*ai_v))
    bs.config_can_publishing(box, True, False, False)
    bs.hil_mode(box, False)
    dio_directions = 8*[1]
    dio_states = 4*[0]+4*[0]
    bs.dio_set(box, dio_directions, dio_states)
    sleep(1)
    print("DIO1:\t{:b} | DIO2:\t{:b} | DIO3:\t{:b} | DIO4:\t{:b} \nDIO5:\t{:b} | DIO6:\t{:b} | DIO7:\t{:b} | DIO8:\t{:b}".format(*bs.readback_dio(box)))
    sleep(1)
    dio_states= 4*[1]+4*[1]
    bs.dio_set(box, dio_directions, dio_states)
    print("DIO1:\t{:b} | DIO2:\t{:b} | DIO3:\t{:b} | DIO4:\t{:b} \nDIO5:\t{:b} | DIO6:\t{:b} | DIO7:\t{:b} | DIO8:\t{:b}".format(*bs.readback_dio(box)))