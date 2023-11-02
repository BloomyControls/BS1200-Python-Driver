from bs1200 import BS1200
import time

u = [1]
with BS1200(u, 'PCAN_USBBUS1', 1000000) as units:
	for unit in range(1,len(u)+1):
		print("Testing unit "+str(unit))
		units.set_V_all(unit, 0) # set all cells to 0V
		print("Setting all unit "+str(unit)+" cells to 0V")
		print("Setting current limits on unit "+str(unit)+" to 500mA src/sink")
		units.set_I_all(unit, 0.5, 0.5)
		print("Enabling all cells on unit "+str(unit))
		units.cell_enable_all(unit, True)
		for cell in range(1,13):
				units.set_cell_I_source(unit, cell, 0.5)
				units.set_cell_I_sink(unit, cell, 0.5)
		volts = units.readback_V_all(unit)
		amps = units.readback_I_all(unit)
		print(units.v_fmt_txt.format(*volts))
		print(units.i_fmt_txt.format(*amps))
	input("All units initialized-- enter to continue")

	for unit in range(1,len(u)+1):
		for cell in range(1,13):
			print("\nUnit "+str(unit)+" cell "+str(cell))
			units.set_cell_V(unit, cell, 4.5)
			units.set_cell_I_source(unit, cell, 0.5)
			units.set_cell_I_sink(unit, cell, 0.5, wait=True) #wait set to True for 10 ms delay
			volts = units.readback_V_all(unit)
			amps = units.readback_I_all(unit)
			print("Cell voltages:\n"+units.v_fmt_txt.format(*volts))
			print("Cell currents:\n"+units.i_fmt_txt.format(*amps))
			input("Measure current w/dmm on cell "+str(cell)+" unit "+str(unit))
			units.set_cell_V(unit, cell, 0)
			input("Press enter to continue to next cell")