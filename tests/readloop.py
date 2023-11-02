from time import sleep
import bs1200

with bs1200.BS1200([1], 'PCAN_USBBUS1', 1000000) as bs:
	#sleep(0.01)
	bs.query_system_status(1)
	bs.set_V_all(1, 0.00)
	bs.set_I_all(1, 0.5, 0.5)
	bs.cell_enable_all(1, True, True)
	#sleep(0.05)
	volts = bs.readback_V_all(1)
	amps = bs.readback_I_all(1)
	print('Cell Voltages:\n' + bs.v_fmt_txt.format(*volts))    
	print('Cell Currents:\n' + bs.i_fmt_txt.format(*amps))
	sp = 0.1
	while(sp <= 5.0):
		print("\n\nSettings all to " + str(sp) + " V") 
		bs.set_V_all(1, sp, True)
		volts = bs.readback_V_all(1)
		print('Cell Voltages:\n' + bs.v_fmt_txt.format(*volts))   
		sp += 0.1
	print("Resetting to 0 and disabling all cells")
	bs.set_V_all(1, 0.00)
	bs.set_I_all(1, 0.0, 0.0)
	bs.cell_enable_all(1, False)
	volts = bs.readback_V_all(1)
	amps = bs.readback_I_all(1)
	print('Cell Voltages:\n' + bs.v_fmt_txt.format(*volts))    
	print('Cell Currents:\n' + bs.i_fmt_txt.format(*amps))