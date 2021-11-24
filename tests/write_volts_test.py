from time import sleep
import sys
sys.path.append('src')
import bs1200

loop = True

with bs1200.BS1200([1]) as bs:
    bs.query_system_status(1)
    bs.set_V_all(1, 0.00)
    bs.set_I_all(1, 0.5, 0.5)
    bs.cell_enable_all(1, True)
    sleep(1)
    volts = bs.readback_V_all(1)
    print(bs.cell_v_output_txt.format(*volts))
    if loop:
        for i in range(1,13):
            print('---------------\nSetting Cell '+str(i)+' to 1 Volt')
            bs.set_cell_V(1, i, 1.00)
            sleep(1)
            volts = bs.readback_V_all(1)
            amps = bs.readback_I_all(1)
            print('Cell Voltages:\n' + bs.cell_v_output_txt.format(*volts))    
            print('Cell Currents:\n' + bs.cell_i_output_txt.format(*amps))
    else: 
        if bs.set_V_all(1, 4.00): print("Setting all cells to 4.00 V")
        sleep(1)
        volts = bs.readback_V_all(1)
        amps = bs.readback_I_all(1)
        print('Cell Voltages:\n' + bs.cell_v_output_txt.format(*volts))    
        print('Cell Currents:\n' + bs.cell_i_output_txt.format(*amps))