from time import sleep
from bs1200 import BS1200

box = 1
with BS1200([box]) as bs:
    bs.query_system_status(box)
    #print(bs.rx_cache)
    bs.set_cell_V(1, 1, 4)
    bs.cell_enable(1,1, True)
    sleep(0.5)
    print(bs.readback_cell_V(1,1))
    bs.cell_enable_all(1, False)