from time import sleep
import bs1200

loop = True

with bs1200.BS1200([1]) as bs:
    bs.query_system_status(1)
    bs.set_V_all(1, 0.00)
    bs.set_I_all(1, 0.5, 0.5)
    bs.cell_enable_all(1, True)
    sleep(1)
    volts = bs.readback_V_all(1)
    print(bs.v_fmt_txt.format(*volts))
    if loop:
        for i in range(1,13):
            print('---------------\nSetting Cell '+str(i)+' to 2.5 Volt')
            bs.set_cell_V(1, i, 2.50)
            sleep(1)
            volts = bs.readback_V_all(1)
            amps = bs.readback_I_all(1)
            print('Cell Voltages:\n' + bs.v_fmt_txt.format(*volts))    
            print('Cell Currents:\n' + bs.i_fmt_txt.format(*amps))
    else: 
        if bs.set_V_all(1, 4.00): print("Setting all cells to 4.00 V")
        sleep(1)
        volts = bs.readback_V_all(1)
        amps = bs.readback_I_all(1)
        print('Cell Voltages:\n' + bs.v_fmt_txt.format(*volts))    
        print('Cell Currents:\n' + bs.i_fmt_txt.format(*amps))