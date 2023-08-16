from struct import unpack
import sys
from can.interfaces.pcan import pcan
import can
from can.message import Message
import bs1200.can_frames as ff

def _get_message(msg): return msg

class BS1200(object):
    """
    Communicates with Bloomny BS1200 via Peak Systems PCAN-FD USB Interface 
    """

    def __init__(self, unit_ids: list) -> None:
        cfg = {'fd': False, 'f_clock_mhz' : 20}
        unit_ids.sort()
        self.box_ids = []
        for b in unit_ids:
            if b in range(1,16):
                self.box_ids.append(b)
            else:
                raise IndexError('Invalid BS1200 Box ID: %d' % b)
                
        self.bus = pcan.PcanBus(channel='PCAN_USBBUS1', bitrate=1000000, args = cfg)
        self.buffer = can.BufferedReader()
        self.notifier = can.Notifier(self.bus, [_get_message, self.buffer])

    def __enter__(self):
        return self

    def __exit__(self, exception_type, execption_val, tb):
        self.close()
        if exception_type is not None:
            sys.tracebacklimit.print_exception(exception_type, execption_val, tb)
            return False
        else:
            return True
    #text string that may be used to format the cell voltage readback for std output
    # use string.format(*voltage_list) to format a list of 12 float values to each cell 
    cell_v_output_txt = ("Cell 1:\t{:5f} V\t| Cell 2:\t{:5f} V\t| Cell 3:\t{:5f} V\t| Cell 4:\t{:5f} V |"+
                       "\nCell 5:\t{:5f} V\t| Cell 6:\t{:5f} V\t| Cell 7:\t{:5f} V\t| Cell 8:\t{:5f} V |"+
                       "\nCell 9:\t{:5f} V\t| Cell 10:\t{:5f} V\t| Cell 11:\t{:5f} V\t| Cell 12:\t{:5f} V |")
    #text string that may be used to format the analog input voltage readback for std output
    # use string.format(*ai_volt_list) to format a list of 8 float values to each analog input 
    ai_v_output_txt = ("AI 1:\t{:5f} V\t| AI 2:\t{:5f} V\t| AI 3:\t{:5f} V\t| AI 4:\t{:5f} V |"+
                     "\nAI 5:\t{:5f} V\t| AI 6:\t{:5f} V\t| AI 7:\t{:5f} V\t| AI 8:\t{:5f} V |")
    
    #text string that may be used to format the cell current readback for std output
    # use string.format(*current_list) to format a list of 12 float values to each cell 
    cell_i_output_txt = ("Cell 1:\t{:5f} A\t| Cell 2:\t{:5f} A\t| Cell 3:\t{:5f} A\t| Cell 4:\t{:5f} A"+
                    "\nCell 5:\t{:5f} A\t| Cell 6:\t{:5f} A\t| Cell 7:\t{:5f} A\t| Cell 8:\t{:5f} A"+
                    "\nCell 9:\t{:5f} A\t| Cell 10:\t{:5f} A\t| Cell 11:\t{:5f} A\t| Cell 12:\t{:5f} A")
    
    def scale_volts(self, voltsIn, recieving : bool):
        """
        Helper method to scale voltage value from or to microvolts.
        (for recieved vals) Set recieving True to scale from millivolts (int) -> volts 
         (for transmitted vals) Set False to scale from volts (float) -> millivolts (int)
        """
        return (float(voltsIn*0.0001)) if recieving  else (int(voltsIn/0.0001))

    def scale_current(self, currentIn, recieving: bool):
        """
        Helper method to scale current values from Amps to scaled values used by BS1200
        set to_eng_units.
        True to convert Scaled milliamps -> Amps (for recieved vals)
        set False to convert Amps -> scaled Milliamps (to transmit)
        """
        return (((currentIn/10) - 3276.8)/1000) if recieving else int((currentIn*10)*1000)

    def close(self):
        self.bus.shutdown()

    def channel_check(self, channel: int) -> bool:
        return True if channel in range(1, 13) else False
    
    def box_id_check(self, boxid) -> bool:
        return True if boxid in self.box_ids else False

    def query_system_status(self, boxid: int):
        """
        """
        if self.box_id_check(boxid):
            try: 
                msg = ff.status(boxid)
                for frame in self.bus:
                    if frame.arbitration_id == msg.arbitration_id:
                        sys_stat = frame
                        break
                if sys_stat:
                    fanstat = sys_stat.data[0]
                    if(fanstat== 16):
                        fanFailStat = 'No Fault'
                    else:
                        fanFailStat = 'Fan Failure Detected'
                    tempSens1 = sys_stat.data[1]
                    tempSens2 = sys_stat.data[2]
                    tempSens3 = sys_stat.data[3]

                    print("Fan Status:", fanFailStat)
                    print("Temp Sensor 1:  "+str(tempSens1)+" °C")
                    print("Temp Sensor 2:  "+str(tempSens2)+" °C")
                    print("Temp Sensor 3:  "+str(tempSens3)+" °C")
            except pcan.PcanError as e:
                print("Error occured querying system status:", e)

    def hil_mode(self, boxid: int, enable_HIL: bool) -> bool:
        """
        Enable or disable the BS1200 in HIL mode. Returns PCAN bus OK status.
        Once set, the Battery Simulator will execute only the commands defined as active in HIL mode.
        By default all auxiliary configuration channels are set to disabled during HIL mode. 
        In order to change this option, the configuration frame must be used. 
        Note, the Configure frame is not supported in HIL mode, so this must be sent while HIL mode is disabled.
        """
        if self.box_id_check(boxid):
            tx_msg = ff.hil_mode_trig(boxid, enable_HIL)
            try:
                self.bus.send(tx_msg)
                return self.bus.status_is_ok()
            except pcan.PcanError as e:
                print("Error sending HIL mode trigger message:", e)

    def config_can_publishing(self, boxid: int, dio_en: bool, ao_en: bool, ai_en: bool):
        if self.box_id_check(boxid):
            tx_msg = ff.config(boxid, dio_hil_set_en=dio_en, ao_hil_set_en=ao_en,
                                dio_hil_bcast_en=dio_en, ai_1_4_bcast_en=ai_en, 
                                ai_5_8_bcast_en=ai_en, cal_mode=False)
            try:
                self.bus.send(tx_msg)
                return self.bus.status_is_ok()
            except pcan.PcanError as e:
                print("Error sending HIL publishing configuration message to BS1200:", e)

    def cell_enable(self, boxid: int, channel: int, status: bool):
        if self.box_id_check(boxid):
            frame = ff.cell_enable(boxid, channel, status)
            try:
                self.bus.send(frame)
                return self.bus.status_is_ok()
            except pcan.PcanError as e:
                print("Error sending cell enable message:", e)
    
    def cell_enable_all(self, boxid: int, status: bool):
        if self.box_id_check(boxid):
            frame = ff.cell_enable_all(boxid, status)
            try:
                self.bus.send(frame)
                return self.bus.status_is_ok()
            except pcan.PcanError as e:
                print("Error sending cell enable message:", e)

    def set_cell_V(self, boxid: int, channel: int, voltage: float) -> Message:
        """
        Set an individual cell (1-12) to designated voltage value input range 0.00 to 5.00 Volts
        """
        if self.box_id_check(boxid):
            volts = self.scale_volts(voltage, False)
            tx_msg = ff.cell_voltage_setpoint(boxid, channel, volts)
            try:
                self.bus.send(msg=tx_msg)
                #use blocking receive function until rx message is recieved
                return self.bus.status_is_ok()
            except can.PcanError as e:
                print("An error occurred communicating with the BS1200:", e)

    def set_V_all(self, boxid, tgt_volt: float):
        """
        Set the cell voltage for Cells 1-12, valid inputs from 0.00 to 5.00 Volts
        """
        if self.box_id_check(boxid):    
            scaled_volts = self.scale_volts(tgt_volt, False)
            tx_msg = ff.cell_voltage_set_all(boxid, scaled_volts)
            try:
                self.bus.send(tx_msg, timeout=None)
                return self.bus.status_is_ok()
            except pcan.PcanError as e:
                print("An error occurred communicating set cell v all the BS1200:", e)

    def readback_cell_V(self, boxid: int, channel: int) -> float:
        """
        Readback voltage value of designated cell channel 1-12. 
        """
        if self.box_id_check(boxid):
            readbacks = [ff.cell_V_get_1_4(boxid), 
                        ff.cell_V_get_5_8(boxid), 
                        ff.cell_V_get_9_12(boxid)]
            frame_i = channel // 4
            cell_i = (channel-1) % 4
            try:
                for msg in self.bus:
                    if msg.arbitration_id == readbacks[frame_i].arbitration_id:
                        rx_msg = msg
                        break
                cell_volts = self.scale_volts(unpack('<H', rx_msg.data[cell_i*2:cell_i*2+2])[0], True)
                return cell_volts
            except pcan.PcanError as e:
                print("Error getting cell "+str(channel)+" Voltage: ", e)

    def readback_V_all(self, boxid) -> list:
        """
        Return list of voltage values (V) for all cell channels.
        """
        if self.box_id_check(boxid):
            readbacks= [ff.cell_V_get_1_4(boxid),
                        ff.cell_V_get_5_8(boxid),
                        ff.cell_V_get_9_12(boxid)]
            cell_volts = 12*[None]
            rx_frames = [False, False, False]
            for msg in self.bus:
                if msg.arbitration_id == readbacks[0].arbitration_id:
                    rx_frames[0] = msg
                if msg.arbitration_id == readbacks[1].arbitration_id:
                    rx_frames[1] = msg
                if msg.arbitration_id == readbacks[2].arbitration_id:
                    rx_frames[2] = msg
                if False not in rx_frames:
                    break
            for channel in range(1,13):
                frame, start, end = ((channel-1)//4, 2*((channel-1)%4), 2*((channel-1)%4)+2)
                cell_volts[channel-1] = self.scale_volts(unpack('<H', rx_frames[frame].data[start:end])[0], True)     
            return cell_volts

    def set_cell_I_sink(self, boxid: int, channel: int, sink_current: float) -> Message:
        """
        Construct and send message to set an individual cell current sinking value
        """
        if self.box_id_check(boxid):
            amps = self.scale_current(sink_current, False)
            tx_msg = ff.cell_current_sink_setpoint(boxid, channel, amps)
            try:
                self.bus.send(msg=tx_msg)
                #use blocking receive function until rx message is recieved
                return self.bus.status_is_ok()
            except can.PcanError as e:
                print("An error occurred communicating with the BS1200:", e)

    def set_cell_I_source(self, boxid: int, channel: int, source_current: float) -> Message:
        """
        Construct and send message to set an individual cell current sourcing value
        """
        if self.box_id_check(boxid):
            amps = self.scale_current(source_current, False)
            tx_msg = ff.cell_current_source_setpoint(boxid, channel, amps)
            try:
                self.bus.send(msg=tx_msg)
                #use blocking receive function until rx message is recieved
                return self.bus.status_is_ok()
            except can.PcanError as e:
                print("An error occurred communicating with the BS1200:", e)
    
    def set_I_all(self, boxid: int, sink_i: float, source_i: float):
        """
        Set the sink and sourcing current limits for all cells. Valid in range 0-0.5 A
        """
        if self.box_id_check(boxid):
            sink_val = self.scale_current(sink_i, False) #convert to mA before applying the scaling factor
            source_val = self.scale_current(source_i, False)
            tx_msg = ff.cell_current_set_all(boxid, sink_val, source_val)
            try:
                self.bus.send(tx_msg)
            except pcan.PcanError as e:
                print("error setting sink and source limits for all cells:", e)
    
    def readback_cell_I(self, boxid: int, channel: int) -> float:
        """
        Readback current value (in Amps) of designated cell channel 1-12. 
        """
        if self.box_id_check(boxid):
            readbacks = [ff.cell_I_get_1_4(boxid), 
                        ff.cell_I_get_5_8(boxid), 
                        ff.cell_I_get_9_12(boxid)]
            frame_i, cell_i  = (channel-1) // 4, (channel-1) % 4
            try:
                for msg in self.bus:
                    if msg.arbitration_id == readbacks[frame_i].arbitration_id:
                        rx_msg = msg
                        break
                cell_amps = self.scale_current(int.from_bytes(rx_msg.data[cell_i*2:cell_i*2+2], 'little'), True)
                return cell_amps
            except pcan.PcanError as e:
                print("Error getting cell "+str(channel)+" Current: ", e)
                
    def readback_I_all(self, boxid: int) -> list:
        """
        Return current readbacks (A) for all cell channels.
        """
        if self.box_id_check(boxid):
            readbacks = [ff.cell_I_get_1_4(boxid),
                        ff.cell_I_get_5_8(boxid), 
                        ff.cell_I_get_9_12(boxid)]
            cell_currents = 12*[None]
            rx_frames = [False, False, False]
            for msg in self.bus:
                if msg.arbitration_id == readbacks[0].arbitration_id:
                    rx_frames[0] = msg
                if msg.arbitration_id == readbacks[1].arbitration_id:
                    rx_frames[1] = msg
                if msg.arbitration_id == readbacks[2].arbitration_id:
                    rx_frames[2] = msg
                if False not in rx_frames:
                    break
            for channel in range(1,13):
                frame, start, end = ((channel-1)//4, 2*((channel-1)%4), 2*((channel-1)%4)+2)
                cell_currents[channel-1] = self.scale_current(int.from_bytes(rx_frames[frame].data[start:end], 'little'), True)
            return cell_currents

    def readback_ai_v(self, boxid: int, channel: int) -> float:
        """
        Readback analog input voltage value of designated channel 1-8 
        """
        if self.box_id_check(boxid) and (channel in range(1,9)):
            readbacks = [ff.ai_get_1_4(boxid), ff.ai_get_5_8(boxid)]
            frame_i = channel // 4
            cell_i = (channel-1) % 4
            try:
                for msg in self.bus:
                    if msg.arbitration_id == readbacks[frame_i].arbitration_id:
                        rx_msg = msg
                        break
                ai_volts = self.scale_volts(unpack('<H', rx_msg.data[cell_i*2:cell_i*2+2])[0], True)
                return ai_volts
            except pcan.PcanError as e:
                print("Error getting AI Channel "+str(channel)+" Voltage: ", e)

    def readback_ai_all(self, boxid: int) -> list:
        """
        Readback Analog Input Channels 1-8
        """
        if self.box_id_check(boxid):
            readbacks = [ff.ai_get_1_4(boxid), ff.ai_get_5_8(boxid)]
            rx_frames = [False, False]
            ai_volts = 8*[None]
            for msg in self.bus:
                if msg.arbitration_id == readbacks[0].arbitration_id:
                    rx_frames[0] = msg
                if msg.arbitration_id == readbacks[1].arbitration_id:
                    rx_frames[1] = msg
                if False not in rx_frames:
                    break            
            for channel in range(1,9):
                frame, start, end = ((channel-1)//4, 2*((channel-1)%4), 2*((channel-1)%4)+2)
                ai_volts[channel-1] = self.scale_volts(int.from_bytes(rx_frames[frame].data[start:end], 'little'), True)
            return ai_volts

    def ao_set(self, boxid: int, AO1_Voltage: float, AO2_Voltage: float) -> bool:
        """
        Set the BS1200's Analog Output voltage setpoints. Valid range from 0-5 V.
        """
        ao1_volts = self.scale_volts(AO1_Voltage, False)
        ao2_volts = self.scale_volts(AO2_Voltage, False)
        tx_msg = ff.ao_set_1_2(boxid, ao1_volts, ao2_volts)
        try:
            self.bus.send(tx_msg, timeout= None)
            return self.bus.status_is_ok()
        except pcan.PcanError as e:
            print("Error occurred sending AO setpoint message to BS1200 ID {:d}:".format(boxid), e)

    def dio_set(self, boxid: int, dio_dir: list, dio_en: list) -> bool:
        """
        Set the direction of Digital IO Channels 1-8. 
        dio_dir: List of Boolean values designating direction of each DIO Channel.
                 Set 1 to configure as Output, 0 to configure as Input
        dio_en: Enables the DIO line when the direction is also set to True (1).
        """
        tx_msg = ff.dio_set_1_8(boxid, [bool(a) for a in dio_en], [bool(a) for a in dio_dir])
        try:
            self.bus.send(tx_msg)
            print(tx_msg)
            return self.bus.status_is_ok()
        except pcan.PcanError as e:
            print("Error occurred transmitting DIO Set frame to BS1200:", e)
        
    def readback_dio(self, boxid) -> list:
        """
        Returns state of Digital Input/Output Lines
        """
        rx = ff.dio_states_1_8(boxid)
        dio_read = None
        try:
            for msg in self.bus:
                if msg.arbitration_id == rx.arbitration_id:
                    dio_read = msg
                    print(msg)
                    break
            if dio_read:
                states = format(dio_read.data[0], '08b')
                dio_states = [False if bit == '0' else True for bit in states]
                return reversed(dio_states)
        except pcan.PcanError as e:
            print("Error reading DIO states on BS1200:", e)
