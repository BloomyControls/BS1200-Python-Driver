from struct import pack, unpack
from can import Message

def cell_V_set_1_4(box_id: int, cell_1_4_v: list[float]) -> Message:
    """
    Sets the Voltage Setpoints for Cells 1-4, range 0 to 5 V
    """
    try:
        arb_id = 160 + box_id
        v_data = pack("<4e", *cell_1_4_v)
        frame = Message(arbitration_id= arb_id,
                        data= v_data,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        
        return frame
    except ValueError as e:
        print("Error generating Cell_Set_V_1_4 message:", e)

def cell_V_set_5_8(box_id: int, cell_5_8_v: list[float]) -> Message:
    """
    Sets the Voltage Setpoints for Cells 1-4, range 0 to 5 V
    """
    try:
        arb_id = 176 + box_id
        v_data = pack("<4e", *cell_5_8_v)
        frame = Message(arbitration_id= arb_id,
                        data= v_data,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        
        return frame
    except ValueError as e:
        print("Error generating Cell_Set_V_5_8 message:", e)

def cell_V_set_9_12(box_id: int, cell_9_12_v: list[float]) -> Message:
    """
    Sets the Voltage Setpoints for Cells 1-4, range 0 to 5 V
    """
    try:
        arb_id = 192 + box_id
        v_data = pack("<4e", *cell_9_12_v)
        frame = Message(arbitration_id= arb_id,
                        data= v_data,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        
        return frame
    except ValueError as e:
        print("Error generating Cell_Set_V_9_12 message:", e)

def hil_mode_trig(box_id: int, enable: bool) -> Message:
    """
    HIL mode start/stop trigger
       Returns a pcan.Message sent to the BS1200 
       to enable/disable HIL mode
       Parameters: 
       --Box ID of the BS1200 unit
       --Enable/disable (True/False) trigger for data payload
    """
    try:
        arb_id = 128 + box_id
        frame = Message(arbitration_id = arb_id,
                        data = bytes([enable]),
                        is_extended_id = False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error generating HIL mode trigger frame:", e)
        return None

def dio_set_1_8(box_id: int, dio_val: list[bool], dio_direction: list[bool]) -> Message:
    """
    Returns message to configure the output 
    value and direction for the Digital IO
    """
    try:
        arb_id = 512 + box_id
        dir_int = sum(2**i for i, v in enumerate(dio_direction) if v)
        en_int  = sum(2**i for i, v in enumerate(dio_val) if v)
        dio_payload = bytearray([en_int, dir_int])
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        data = dio_payload,
                        check = True,
                        is_fd= False
                        )
        return frame

    except ValueError as e:
        print("Error generating DIO Setpoints message:", e)
        return None

def ao_set_1_2(box_id: int, ao1_voltage: float, ao2_voltage: float) -> Message:
    """
    Generate message sent to configure 
    the BS1200 analog output setpoints
    Voltage setpoints are valid in the range 0-5 Volts
    """
    try:
        arb_id = 544 + box_id
        ao1 = pack("<e", ao1_voltage)
        ao2 = pack("<e", ao2_voltage)
        ao_payload = ao1 + ao2 + bytes(4) #pad payload with 4 empty bytes (as seen in CAN DB)
        frame = Message(arbitration_id = arb_id,
                        is_extended_id = False,
                        data = ao_payload,
                        check = True,
                        is_fd= False
                        )
        return frame

    except ValueError as e:
        print("Error generating analog output setpoint message:", e)
        return None

def config(box_id: int, dio_hil_set_en: bool, ao_hil_set_en: bool, dio_hil_bcast_en: bool, 
                         ai_1_4_bcast_en: bool, ai_5_8_bcast_en: bool, cal_mode: bool) -> Message:
    """
    Generate a message to configure the Box Mode and Message Configuration
    """
    try:
        arb_id = 1024 + box_id
        bool_array =[dio_hil_set_en, ao_hil_set_en, False, False, False, False, False, False,            #Bits 0-7
                      dio_hil_bcast_en, ai_1_4_bcast_en, ai_5_8_bcast_en, False, False, False, False, False, #Bits 8-15
                      cal_mode, False, False, False, False, False, False, False]                         #Bits 16-23 
        byte1 = sum(2**i for i, v in enumerate(bool_array[0:7]) if v)
        byte2 = sum(2**i for i, v in enumerate(bool_array[8:15]) if v) 
        byte3 = sum(2**i for i, v in enumerate(bool_array[16:23]) if v) 
        frame = Message(arbitration_id = arb_id,
                        is_extended_id = False,
                        data = bytes([byte1, byte2, byte3]),
                        check = True,
                        is_fd= False 
                        )
        return frame
    except ValueError as e:
        print("Error generating message for box mode and message configuration:", e)
        return None

def cell_current_set_all(box_id, I_sink_all: int, I_source_all: int) -> Message:
    """
    Generates a message to set the source and sinking current for all cells
    """
    try: 
        arb_id = 1125 + box_id
        curr_vals = I_sink_all.to_bytes(2, 'little')+I_source_all.to_bytes(2, 'little')
        frame = Message(arbitration_id= arb_id, 
                        is_extended_id = False, 
                        data = curr_vals, 
                        check = True,
                        is_fd= False
                        )
        return frame
        
    except ValueError as e:
        print("Error constructing cell current set all message:", e)
        return None

def cell_current_sink_setpoint(box_id, channel: int, I_sink: float) -> Message:
    """
    Generates a message to set the sink current of a single channel
    """
    try: 
        arb_id = 1184 + box_id
        sink_val = I_sink.to_bytes(2, 'little')
        
        frame = Message(arbitration_id= arb_id, 
                        is_extended_id = False, 
                        data = bytes([channel-1])+sink_val, 
                        check = True,
                        is_fd= False
                        )
        return frame

    except ValueError as e:
        print("Error constructing set cell sinking current message:", e)
        return None

def cell_current_source_setpoint(box_id, channel: int, I_source: float) -> Message:
    """
    Generates a message to set the source current for a signle channel
    """
    try: 
        arb_id = 1200 + box_id
        source_val = I_source.to_bytes(2, 'little')
        frame = Message(arbitration_id= arb_id, 
                        is_extended_id = False,
                        data = bytes([channel-1])+source_val, 
                        check = True,
                        is_fd= False
                        )
        return frame

    except ValueError as e:
        print("Error constructing message to set cell %d to %f: %s" % channel, I_source, e)
        return None

def cell_voltage_set_all(box_id, v_all: float) -> Message:
    """
    Generates a message to set the voltage value for all cells
    """
    try: 
        arb_id = 1280 + box_id
        volt_val = pack("<e", v_all)
        frame = Message(arbitration_id= arb_id, 
                        is_extended_id = False, 
                        data = volt_val, 
                        check = True,
                        is_fd= False
                        )
        return frame

    except ValueError as e:
        print("Error constructing cell current set all message:", e)
        return None


def cell_voltage_setpoint(box_id, channel: int, volt_val: float) -> Message:
    """
    Generates a message to set the source current for a signle channel
    """
    try: 
        arb_id = 1296 + box_id
        source_val = pack("<e", volt_val)
        frame = Message(arbitration_id= arb_id, 
                        is_extended_id = False, 
                        data = bytes([channel-1])+source_val, 
                        check = True,
                        is_fd= False
                        )
        return frame

    except ValueError as e:
        print("Error constructing message to set cell %d to %f volts: %s" % channel, volt_val, e)
        return None

def cell_enable_all(box_id: int, enable: bool) -> Message:
    """
    Generate message to enable or disable all cells
    """
    try:
        arb_id = 1344 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        data = bytes([enable]),
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing cell enable all message:", e)
        return None

def cell_enable(box_id: int, channel: int, enable: bool) -> Message:
    """
    Generate message to enable or disable cell
    """
    try:
        arb_id = 1360 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        data = bytes([channel-1])+bytes([enable]),
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing cell enable message for channel %d: %s" % channel, e)
        return None

def status(box_id: int) -> Message:
    """
    Generates empty bs1200 status frame
    """
    try:
        arb_id = 256 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing bs1200 status frame: ", e)
        return None

def cell_V_get_1_4(box_id: int) -> Message:
    """
    Generate frame to capture cell voltage readback for cells 1-4
    """
    try:
        arb_id = 288 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing Cell_V_Readback_1_4 frame", e)
        
def cell_V_get_5_8(box_id: int) -> Message:
    """
    Generate frame to capture cell voltage readback for cells 5-8
    """
    try:
        arb_id = 304 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing Cell_V_Readback_5_8 frame", e)

def cell_V_get_9_12(box_id: int) -> Message:
    """
    Generate frame to capture cell voltage readback for cells 9-12
    """
    try:
        arb_id = 320 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing Cell_V_Readback_9_12 frame", e)

def cell_I_get_1_4(box_id: int) -> Message:
    """
    Generate frame to capture cell current readback for cells 1-4
    """
    try:
        arb_id = 384 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing Cell_I_Readback_1_4 frame", e)
        
def cell_I_get_5_8(box_id: int) -> Message:
    """
    Generate frame to capture cell current readback for cells 5-8
    """
    try:
        arb_id = 400 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing Cell_I_Readback_5_8 frame", e)

def cell_I_get_9_12(box_id: int) -> Message:
    """
    Generate frame to capture cell current readback for cells 9-12
    """
    try:
        arb_id = 416 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing Cell_I_Readback_9_12 frame", e)

def dio_states_1_8(box_id: int) -> Message:
    """
    Generate frame to readback DIO States for channels 1 to 8
    """
    try:
        arb_id = 640 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing DIO_Readback_1_8 frame", e)

def ai_get_1_4(box_id: int) -> Message:
    """
    Generate frame to readback analog input channels 1 to 4
    """
    try:
        arb_id = 672 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing AI_Readback_1_4 frame", e)

def ai_get_5_8(box_id: int) -> Message:
    """
    Generate frame to readback analog input channels 5 to
    """
    try:
        arb_id = 688 + box_id
        frame = Message(arbitration_id = arb_id,
                        is_extended_id= False,
                        check = True,
                        is_fd= False
                        )
        return frame
    except ValueError as e:
        print("Error constructing AI_Readback_5_8 frame", e)



