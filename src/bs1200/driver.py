from struct import unpack
import sys
from can.interfaces.pcan import pcan
import can
from can.message import Message
import bs1200.can_frames as ff
from time import sleep



class BS1200(object):
    """
    Communicates with Bloomy BS1200 via Peak Systems PCAN-FD USB Interface (requires Peak chardev driver)
    Class constructor has the following arguments:
        - unit_ids     (required): list of integer box ids assigned to BS1200s on the connected CAN Bus
        - pcan_channel (optional): Defaults to 'PCAN_USBBUS1'. 
                                   Provide this argument if another PCAN channel name is used
        - bit_rate     (optional): Bitrate/Baudrate defaults to BS1200 default of 1000000. 
                                   Only provide if BS1200 Unit(s) are configured to a different baudrate
        - delay_ms     (optional): Delay in milliseconds to be used in can_wait() calls 
                                   optionally made after sending CAN frames to BS1200 unit.
                                   Defaults to 10 ms
    """
    
    def _get_message(self, msg):
        self.rx_cache[msg.arbitration_id] = msg

    def __init__(self, unit_ids: list, pcan_channel = 'PCAN_USBBUS1', bit_rate = 1000000, delay_ms = 10) -> None:
        #Give BoxIDs OR Ip Addrs and init interface based on non-default value
        cfg = {'fd': False, 'f_clock_mhz' : 20}
        unit_ids.sort()
        self.box_ids = []
        for b in unit_ids:
            if b in range(1,16):
                self.box_ids.append(b)
            else:
                raise IndexError('Invalid BS1200 Box ID: %d' % b)
        self.rx_cache = ff.init_frame_dict(self.box_ids)   
        self.bus = pcan.PcanBus(channel = pcan_channel, bitrate = bit_rate, args = cfg)
        #DEBUG test if we need these to operate iterative read
        self.buffer = can.BufferedReader()
        self.notifier = can.Notifier(self.bus, [self._get_message, self.buffer])
        self.publish_delay = delay_ms / 1000 #delay to use when using can_wait()
        sleep(0.05) #sleep for frame buffer to populate
    def __enter__(self):
        return self

    def __exit__(self, exception_type, execption_val, tb):
        self.close()
        if exception_type is not None:
            sys.tracebacklimit.print_exception(exception_type, execption_val, tb)
            return False
        else:
            return True
        
    """
    text string that may be used to format the cell voltage readback for std output
    use string.format(*voltage_list) to format a list of 12 float values to each cell 
    """
    v_fmt_txt = ("Cell 1:\t{:5f} V\t| Cell 2:\t{:5f} V\t| Cell 3:\t{:5f} V\t| Cell 4:\t{:5f} V |"+
                       "\nCell 5:\t{:5f} V\t| Cell 6:\t{:5f} V\t| Cell 7:\t{:5f} V\t| Cell 8:\t{:5f} V |"+
                       "\nCell 9:\t{:5f} V\t| Cell 10:\t{:5f} V\t| Cell 11:\t{:5f} V\t| Cell 12:\t{:5f} V |")
    """
    text string that may be used to format the analog input voltage readback for std output
    use string.format(*ai_volt_list) to format a list of 8 float values to each analog input 
    """
    ai_fmt_txt = ("AI 1:\t{:5f} V\t| AI 2:\t{:5f} V\t| AI 3:\t{:5f} V\t| AI 4:\t{:5f} V |"+
                     "\nAI 5:\t{:5f} V\t| AI 6:\t{:5f} V\t| AI 7:\t{:5f} V\t| AI 8:\t{:5f} V |")
    
    """
    #text string that may be used to format the cell current readback for std output
    use string.format(*current_list) to format a list of 12 float values to each cell 
    """
    i_fmt_txt = ("Cell 1:\t{:5f} A\t| Cell 2:\t{:5f} A\t| Cell 3:\t{:5f} A\t| Cell 4:\t{:5f} A |"+
                       "\nCell 5:\t{:5f} A\t| Cell 6:\t{:5f} A\t| Cell 7:\t{:5f} A\t| Cell 8:\t{:5f} A |"+
                       "\nCell 9:\t{:5f} A\t| Cell 10:\t{:5f} A\t| Cell 11:\t{:5f} A\t| Cell 12:\t{:5f} A |")
    
    def can_wait(self):
        sleep(self.publish_delay)
    
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
        """
        Calls pcan bus shutdown procedure
        """
        self.bus.shutdown()

    def reset(self):
        print("Resetting PCAN Bus interface...")
        print("Bus Reset" if self.reset() else "Error resetting PCAN Bus")

    def channel_check(self, channel: int) -> bool:
        return True if channel in range(1, 13) else False
    
    def box_id_check(self, boxid) -> bool:
        return True if boxid in self.box_ids else False

    def query_system_status(self, boxid: int, printout = True):
        """
        Read status frame from BS1200 to get Fan Fault status and Temperature Sensor values.
        Prints output by default `printout` argument, and returns array of Temperature Sensor values in °C
        """
        if self.box_id_check(boxid):
            try: 
                sys_stat = self.rx_cache[256+boxid]
                fanstat = sys_stat.data[0]
                if(fanstat== 16):
                    fanFailStat = 'No Fault'
                else:
                    fanFailStat = 'Fan Failure Detected'
                tempSens1 = sys_stat.data[1]
                tempSens2 = sys_stat.data[2]
                tempSens3 = sys_stat.data[3]
                if(printout):
                    print("Fan Status:", fanFailStat)
                    print("Temp Sensor 1:  "+str(tempSens1)+" °C")
                    print("Temp Sensor 2:  "+str(tempSens2)+" °C")
                    print("Temp Sensor 3:  "+str(tempSens3)+" °C")
                
                return [tempSens1, tempSens2, tempSens3]
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("Error occured querying system status:", e)
                self.reset()

    def hil_mode(self, boxid: int, enable_HIL: bool, wait: bool = False) -> bool:
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
                if(wait): 
                    self.can_wait()
                return self.bus.status_is_ok()
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("Error sending HIL mode trigger message:", e)
                self.reset()

    def config_can_publishing(self, boxid: int, dio_en: bool, ao_en: bool, ai_en: bool, wait: bool = False):
        if self.box_id_check(boxid):
            tx_msg = ff.config(boxid, dio_hil_set_en=dio_en, ao_hil_set_en=ao_en,
                                dio_hil_bcast_en=dio_en, ai_1_4_bcast_en=ai_en, 
                                ai_5_8_bcast_en=ai_en, cal_mode=False)
            try:
                self.bus.send(tx_msg)
                if(wait): 
                    self.can_wait()
                return self.bus.status_is_ok()
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("Error sending HIL publishing configuration message to BS1200:", e)
                self.reset()

    def cell_enable(self, boxid: int, channel: int, status: bool, wait: bool = False):
        """
        Send command to enable/disable a specified cell `channel`
        Pass True as `status` to enable, False to disable
        """
        if self.box_id_check(boxid):
            frame = ff.cell_enable(boxid, channel, status)
            try:
                self.bus.send(frame)
                if(wait): 
                    self.can_wait()
                return self.bus.status_is_ok()
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("Error sending cell enable message:", e)
                self.reset()
    
    def cell_enable_all(self, boxid: int, status: bool, wait: bool = False):
        """
        Send command to enable/disable all cell channels
        Pass True as `status` to enable, `False` to disable
        """
        if self.box_id_check(boxid):
            frame = ff.cell_enable_all(boxid, status)
            try:
                self.bus.send(frame)
                if(wait): 
                    self.can_wait()
                return self.bus.status_is_ok()
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("Error sending cell enable message:", e)
                self.reset()

    def set_cell_V(self, boxid: int, channel: int, voltage: float, wait: bool = False) -> Message:
        """
        Set an individual cell `channel` (1-12) to designated `voltage` value input range 0.00 to 5.00 Volts
        """
        if self.box_id_check(boxid):
            volts = self.scale_volts(voltage, False)
            tx_msg = ff.cell_voltage_setpoint(boxid, channel, volts)
            try:
                #use blocking receive function until rx message is recieved
                self.bus.send(msg=tx_msg)
                if(wait): 
                    self.can_wait()
                return self.bus.status_is_ok()
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("An error occurred communicating with the BS1200:")
                self.reset() #TODO implement everywhere
                        

    def set_V_all(self, boxid, tgt_volt: float, wait: bool = False) -> bool:
        """
        Set the cell voltage for Cells 1-12, valid inputs from 0.00 to 5.00 Volts
        """
        if self.box_id_check(boxid):    
            scaled_volts = self.scale_volts(tgt_volt, False)
            tx_msg = ff.cell_voltage_set_all(boxid, scaled_volts)
            try:
                self.bus.send(tx_msg, timeout=None)
                if(wait): 
                    self.can_wait()
                return self.bus.status_is_ok()
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("An error occurred communicating set cell v all the BS1200:", e)
                self.reset()

    def readback_cell_V(self, boxid: int, channel: int) -> float:
        """
        Readback voltage value of designated cell channel 1-12. 
        """
        if self.box_id_check(boxid):
            try:
                readbacks = [self.rx_cache[288+boxid], 
                             self.rx_cache[304+boxid], 
                             self.rx_cache[320+boxid]]
                frame_i, cell_i  = (channel-1) // 4, (channel-1) % 4
                rx_msg = readbacks[frame_i]
                cell_volts = self.scale_volts(unpack('<H', rx_msg.data[cell_i*2:cell_i*2+2])[0], True)
                return cell_volts
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("Error getting cell "+str(channel)+" Voltage: ", e)
                self.reset()

    def readback_V_all(self, boxid) -> list:
        """
        Return list of voltage values (V) for all cell channels.
        """
        if self.box_id_check(boxid):
            rx_frames = [self.rx_cache[288+boxid], 
                         self.rx_cache[304+boxid], 
                         self.rx_cache[320+boxid]]
            cell_volts = 12*[None]
            
            for channel in range(1,13):
                frame, start, end = ((channel-1)//4, 2*((channel-1)%4), 2*((channel-1)%4)+2)
                cell_volts[channel-1] = self.scale_volts(unpack('<H', rx_frames[frame].data[start:end])[0], True)     
            return cell_volts

    def set_cell_I_sink(self, boxid: int, channel: int, sink_current: float, wait: bool = False) -> Message:
        """
        Construct and send message to set an individual cell current sinking value
        """
        if self.box_id_check(boxid):
            amps = self.scale_current(sink_current, False)
            tx_msg = ff.cell_current_sink_setpoint(boxid, channel, amps)
            try:
                #use blocking receive function until rx message is recieved
                self.bus.send(msg=tx_msg)
                if(wait): 
                    self.can_wait()
                return self.bus.status_is_ok()
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("An error occurred communicating with the BS1200:", e)

    def set_cell_I_source(self, boxid: int, channel: int, source_current: float, wait: bool = False):
        """
        Construct and send message to set an individual cell current sourcing value
        """
        if self.box_id_check(boxid):
            amps = self.scale_current(source_current, False)
            tx_msg = ff.cell_current_source_setpoint(boxid, channel, amps)
            try:
                #use blocking receive function until rx message is recieved
                self.bus.send(msg=tx_msg)
                if(wait): 
                    self.can_wait()
                return self.bus.status_is_ok()
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("An error occurred communicating with the BS1200:", e)
                self.reset()
    
    def set_I_all(self, boxid: int, sink_i: float, source_i: float, wait: bool = False):
        """
        Set the sink and sourcing current limits for all cells. Valid in range 0-0.5 A
        """
        if self.box_id_check(boxid):
            sink_val = self.scale_current(sink_i, False) #convert to mA before applying the scaling factor
            source_val = self.scale_current(source_i, False)
            tx_msg = ff.cell_current_set_all(boxid, sink_val, source_val)
            try:
                self.bus.send(tx_msg)
                if(wait): 
                    self.can_wait()
                return self.bus.status_is_ok()
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("error setting sink and source limits for all cells:", e)
                self.reset()
    
    def readback_cell_I(self, boxid: int, channel: int) -> float:
        """
        Readback current value (in Amps) of designated cell channel 1-12. 
        """
        if self.box_id_check(boxid):
            try:
                readbacks = [self.rx_cache[384+boxid], 
                             self.rx_cache[400+boxid], 
                             self.rx_cache[416+boxid]]
                frame_i, cell_i  = (channel-1) // 4, (channel-1) % 4
                rx_msg = readbacks[frame_i]
                cell_amps = self.scale_current(int.from_bytes(rx_msg.data[cell_i*2:cell_i*2+2], 'little'), True)
                return cell_amps
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("Error getting cell "+str(channel)+" Current: ", e)
                self.reset()
                
    def readback_I_all(self, boxid: int) -> list:
        """
        Return current readbacks (A) for all cell channels.
        """
        if self.box_id_check(boxid):
            rx_frames = [self.rx_cache[384+boxid], 
                         self.rx_cache[400+boxid], 
                         self.rx_cache[416+boxid]]
            cell_currents = 12*[None]
            for channel in range(1,13):
                frame, start, end = ((channel-1)//4, 2*((channel-1)%4), 2*((channel-1)%4)+2)
                cell_currents[channel-1] = self.scale_current(int.from_bytes(rx_frames[frame].data[start:end], 'little'), True)
            return cell_currents

    def readback_ai_v(self, boxid: int, channel: int) -> float:
        """
        Readback analog input voltage value of designated channel 1-8 
        """
        if self.box_id_check(boxid) and (channel in range(1,9)):
            try:
                readbacks = [self.rx_cache[672+boxid], 
                            self.rx_cache[688+boxid]]
                frame_i, cell_i  = (channel-1) // 4, (channel-1) % 4
                rx_msg = readbacks[frame_i]

                ai_volts = self.scale_volts(unpack('<H', rx_msg.data[cell_i*2:cell_i*2+2])[0], True)
                return ai_volts
            except(pcan.PcanError, pcan.PcanCanOperationError) as e:
                print("Error getting AI Channel "+str(channel)+" Voltage: ", e)
                self.reset()

    def readback_ai_all(self, boxid: int) -> list:
        """
        Readback Analog Input Channels 1-8
        """
        if self.box_id_check(boxid):
            rx_frames = [self.rx_cache[672+boxid], 
                         self.rx_cache[688+boxid]]
            ai_volts = 8*[None]
            for channel in range(1,9):
                frame, start, end = ((channel-1)//4, 2*((channel-1)%4), 2*((channel-1)%4)+2)
                ai_volts[channel-1] = self.scale_volts(int.from_bytes(rx_frames[frame].data[start:end], 'little'), True)
            return ai_volts

    def ao_set(self, boxid: int, AO1_Voltage: float, AO2_Voltage: float, wait: bool = False) -> bool:
        """
        Set the BS1200's Analog Output voltage setpoints. Valid range from 0-5 V.
        """
        ao1_volts = self.scale_volts(AO1_Voltage, False)
        ao2_volts = self.scale_volts(AO2_Voltage, False)
        tx_msg = ff.ao_set_1_2(boxid, ao1_volts, ao2_volts)
        try:
            self.bus.send(tx_msg, timeout= None)
            if(wait): 
                self.can_wait()
            return self.bus.status_is_ok()
        except(pcan.PcanError, pcan.PcanCanOperationError) as e:
            print("Error occurred sending AO setpoint message to BS1200 ID {:d}:".format(boxid), e)
            self.reset()

    def dio_set(self, boxid: int, dio_dir: list, dio_en: list, wait: bool = False) -> bool:
        """
        Set the direction of Digital IO Channels 1-8. 
        dio_dir: List of Boolean values designating direction of each DIO Channel.
                 Set 1 to configure as Output, 0 to configure as Input
        dio_en: Enables the DIO line when the direction is also set to True (1).
        """
        tx_msg = ff.dio_set_1_8(boxid, [bool(a) for a in dio_en], [bool(a) for a in dio_dir])
        try:
            self.bus.send(tx_msg)
            if(wait):
                self.can_wait()
            
            return self.bus.status_is_ok()
        except(pcan.PcanError, pcan.PcanCanOperationError) as e:
            print("Error occurred transmitting DIO Set frame to BS1200:", e)
            self.reset()
        
    def readback_dio(self, boxid) -> list:
        """
        Returns state of Digital Input/Output Lines
        """
        try:
            dio_read = self.rx_cache[640+boxid]
            states = format(dio_read.data[0], '08b')
            dio_states = [False if bit == '0' else True for bit in states]
            return dio_states.reverse()
        except(pcan.PcanError, pcan.PcanCanOperationError) as e:
            print("Error reading DIO states on BS1200:", e)
            self.reset()
