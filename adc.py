import EasyMCP2221
import sys
import time
from xmlrpc.server import SimpleXMLRPCServer



# 15V Type B (WAND)
R99=10
R100=249
R101=56
# 15V Type B (15V)
R98=56
R97=249

# 5V Type C (5V)
R191=45.3
R192=56

# shunt (in Ohm)
RShnB=0.0167
RShnC=0.00667

mcp = None
inaB = None
inaC = None
ioext = None

f2on = None
f1on = None

def setup_components():
    global inaB, inaC, ioext, f2on, f1on
    loop = 0
    while True:
        loop += 1
        try:
            inaB = mcp.I2C_Slave(0x40)
            inaC = mcp.I2C_Slave(0x41)
            ioext = mcp.I2C_Slave(0x20)
        except RuntimeError:
            if loop > 4:
                raise RuntimeError("Unable to get I2c slaves")
            mcp.I2C_speed((100000*loop))
            time.sleep(1)
            continue
        else:
            break

    if inaB.is_present():
        inaB.write_register(0x00, bytes.fromhex('4127'))
        inaB.write_register(0x05, bytes.fromhex('0D48'))
    if inaC.is_present():
        inaC.write_register(0x00, bytes.fromhex('4127'))
        inaC.write_register(0x05, bytes.fromhex('1450'))
    if ioext.is_present():
        ioext.write_register(0x03, 0xff)

# Define functions to expose
def read_adc():
    global f2on, f1on
    f2on = ioext.read_register(0x03, 1)
    f1on = mcp.GPIO_read()[0]
    result = {'adc': 'report'}
    try:
        time.sleep(1)

        # config ina to avg 1024 samples
        if inaB.is_present():
            inaB_shnt = inaB.read_register(0x01, 2)
            inaB_vbus = inaB.read_register(0x02, 2)
            inaB_curr = inaB.read_register(0x04, 2)
            inaB_pwr = inaB.read_register(0x03, 2)
        if inaC.is_present():
            inaC_shnt = inaC.read_register(0x01, 2)
            inaC_vbus = inaC.read_register(0x02, 2)
            inaC_curr = inaC.read_register(0x04, 2)
            inaC_pwr = inaC.read_register(0x03, 2)

        values = mcp.ADC_read()
        #print(values)
        result.update( {'B eFUSE': f1on == 1 } )
        result.update( {'B 15V': ((values[2] / 1024) * 3.3 / (R98/(R97+R98))) } )
        if (f1on):
            result.update( {'B WAND': ((values[0] / 1024) * 3.3 / (R101/(R100+R101))) } )
        else:
            result.update( {'B WAND': ((values[0] / 1024) * 3.3 / (R101/(R99+R100+R101))) } )
        result.update( {'B INA Shunt mV': (int.from_bytes(inaB_shnt, byteorder='big') * 0.0025) } )
        result.update( {'B INA VBus': (int.from_bytes(inaB_vbus, byteorder='big') * 0.00125) } )
        result.update( {'B INA Current mA': (int.from_bytes(inaB_curr, byteorder='big') * 0.1) } )
        result.update( {'B INA Power mW': (int.from_bytes(inaB_pwr, byteorder='big') * 2.5) } )

        result.update( {'C eFUSE': f2on & b'\xFE'} )
        result.update( {'C +5V': ((values[1] / 1024) * 3.3 / (R192/(R191+R192))) } )
        result.update( {'C WAND': (int.from_bytes(inaC_vbus, byteorder='big') * 0.00125) } )
        result.update( {'C INA Shunt mV': (int.from_bytes(inaC_shnt, byteorder='big') * 0.0025) } )
        result.update( {'C INA VBus': (int.from_bytes(inaC_vbus, byteorder='big') * 0.00125) } )
        result.update( {'C INA Current mA': (int.from_bytes(inaC_curr, byteorder='big') * 0.15) } )
        result.update( {'C INA Power mW': (int.from_bytes(inaC_pwr, byteorder='big') * 2.5) } )
        print(f"{result}")
        return result

    except EasyMCP2221.exceptions.NotAckError:
        pass

def turn_on():
    mcp.GPIO_write(gp0 = True)
    if ioext.is_present():
        regval = ioext.read_register(0x03, 1)
        print(f"ioext: @0x03: {regval}")
        trgval = bytes(a & b for a, b in zip(regval, b'\xFE'))
        ioext.write_register(0x01, trgval)
        print(f"=> {trgval}")
    return True

def turn_off():
    mcp.GPIO_write(gp0 = False)
    if ioext.is_present():
        regval = ioext.read_register(0x03, 1)
        print(f"ioext: @0x03: {regval}")
        rstval = bytes(a | b for a, b in zip(regval, b'\x01'))
        ioext.write_register(0x01, rstval)
        print(f"=> {rstval}")
    return False

def fx3_rst():
    if ioext.is_present():
        regval = ioext.read_register(0x03, 1)
        print(f"ioext: @0x03: {regval}")
        trgval = bytes(a & b for a, b in zip(regval, b'\xFD'))
        ioext.write_register(0x01, trgval)
        print(f"=> {trgval}")
        time.sleep(1)
        rstval = bytes(a | b for a, b in zip(regval, b'\x02'))
        ioext.write_register(0x01, rstval)
        print(f"=> {rstval}")
    return True

def main():
    global mcp
    mcp = EasyMCP2221.Device()
    mcp.set_pin_function(gp0="GPIO_OUT", gp1="ADC", gp2="ADC", gp3="ADC")
    mcp.ADC_config(ref="VDD")
    mcp.GPIO_write(gp0 = True)
    mcp.I2C_write(0x20, b'\x03\xFF')

    setup_components()
    # Use 127.0.0.1 to avoid Windows localhost DNS resolution delays
    server_address = ("127.0.0.1", 8888)

    with SimpleXMLRPCServer(server_address, logRequests=True) as server:
        print(f"XML-RPC Server listening on http://{server_address[0]}:{server_address[1]}")

        # Register the functions
        server.register_function(read_adc, "read")
        server.register_function(turn_on, "on")
        server.register_function(turn_off, "off")
        server.register_function(fx3_rst, "rst")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            mcp.GPIO_write(gp0 = False)
            ioext.write_register(0x03, 0xff)
            print("\nServer shutting down.")
            sys.exit(0)

if __name__ == "__main__":
    main()
