import EasyMCP2221
import sys
import time

mcp=EasyMCP2221.Device()
if mcp.GPIO_read()[0] is None:
    mcp.set_pin_function(gp0="GPIO_OUT", gp1="ADC", gp2="ADC", gp3="ADC")
    mcp.ADC_config(ref="VDD")
    print("Set Pin Config to OUT ADC ADC ADC")
mcp.GPIO_write(gp0 = False if len(sys.argv) == 1 else (sys.argv[1] == "on"))
print("Pin Configs:")
print(mcp.GPIO_read())
if mcp.GPIO_read()[0] is 0:
    print("GP0 = 0")
    sys.exit(0)
mcp.I2C_write(0x20, b'\x03\xFF')

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

inaB = None
inaC = None
ioext = None
loop = 0

while True:
    loop += 1
    try:
        inaB = mcp.I2C_Slave(0x40) if inaB is None else inaB
        inaC = mcp.I2C_Slave(0x41) if inaC is None else inaC
        ioext = mcp.I2C_Slave(0x20) if ioext is None else ioext
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
    if (len(sys.argv) > 1 and sys.argv[1] == "on"):
        ioext.write_register(0x03, 0xfe)
    else:
        ioext.write_register(0x03, 0xff)
f2on = ioext.read_register(0x03, 1) if ioext.is_present() else None
f1on = mcp.GPIO_read()[0]

try:
    if len(sys.argv) > 2:
        if int(sys.argv[2]) > 0:
            print("ctrl+c to exit")
            for i in range(int(sys.argv[2])):
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
                if (f1on):
                    print("Type B eFUSE: ON")
                    print("+15V: %4.3f V" % ((values[2] / 1024) * 3.3 / (R98/(R97+R98)),))
                    print("WAND: %4.3f V" % ((values[0] / 1024) * 3.3 / (R101/(R100+R101)),))
                else:
                    print("Type B eFUSE: OFF")
                    print("+15V: %4.3f V" % ((values[2] / 1024) * 3.3 / (R98/(R97+R98)),))
                    print("WAND: %4.3f V" % ((values[0] / 1024) * 3.3 / (R101/(R99+R100+R101)),))
                print("INA_B Shunt: %4.3f mV" % (int.from_bytes(inaB_shnt, byteorder='big') * 0.0025))
                print("INA_B VBus: %4.3f V" % (int.from_bytes(inaB_vbus, byteorder='big') * 0.00125))
                print("INA_B Curr: %4.3f mA" % (int.from_bytes(inaB_curr, byteorder='big') * 0.1))
                print("INA_B Pwr: %4.3f mW" % (int.from_bytes(inaB_pwr, byteorder='big') * 2.5))
                print("")
                if (f2on == b'\xfe'):
                    print("Type C eFUSE: ON")
                    print("+5V: %4.3f" % ((values[1] / 1024) * 3.3 / (R192/(R191+R192)),))
                    print("WAND: %4.3f" % (int.from_bytes(inaC_vbus, byteorder='big') * 0.00125))
                else:
                    print("Type C eFUSE: OFF")
                    print("+5V: %4.3f V" % ((values[1] / 1024) * 3.3 / (R192/(R191+R192)),))
                    print("WAND: %4.3f V" % (int.from_bytes(inaC_vbus, byteorder='big') * 0.00125))
                print("INA_C Shunt: %4.3f mV" % (int.from_bytes(inaC_shnt, byteorder='big') * 0.0025))
                print("INA_C VBus: %4.3f V" % (int.from_bytes(inaC_vbus, byteorder='big') * 0.00125))
                print("INA_C Curr: %4.3f mA" % (int.from_bytes(inaC_curr, byteorder='big') * 0.15))
                print("INA_C Pwr: %4.3f mW" % (int.from_bytes(inaC_pwr, byteorder='big') * 2.5))
                print("")

except EasyMCP2221.exceptions.NotAckError:
    pass
except KeyboardInterrupt:
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
    with open("adc.log", "w", encoding="utf-8") as file:
        # Perform file operations here
        #print(values)
        if (f1on):
            file.write("Type B eFUSE: ON\n")
            file.write("+15V: %4.3f V\n" % ((values[2] / 1024) * 3.3 / (R98/(R97+R98)),))
            file.write("WAND: %4.3f V\n" % ((values[0] / 1024) * 3.3 / (R101/(R100+R101)),))
        else:
            file.write("Type B eFUSE: OFF\n")
            file.write("+15V: %4.3f V\n" % ((values[2] / 1024) * 3.3 / (R98/(R97+R98)),))
            file.write("WAND: %4.3f V\n" % ((values[0] / 1024) * 3.3 / (R101/(R99+R100+R101)),))
        file.write("INA_B Shunt: %4.3f mV\n" % (int.from_bytes(inaB_shnt, byteorder='big') * 0.0025))
        file.write("INA_B VBus: %4.3f V\n" % (int.from_bytes(inaB_vbus, byteorder='big') * 0.00125))
        file.write("INA_B Curr: %4.3f mA\n" % (int.from_bytes(inaB_curr, byteorder='big') * 0.1))
        file.write("INA_B Pwr: %4.3f mW\n" % (int.from_bytes(inaB_pwr, byteorder='big') * 2.5))
        file.write("\n")
        if (f2on == b'\xfe'):
            file.write("Type C eFUSE: ON\n")
            file.write("+5V: %4.3f\n" % ((values[1] / 1024) * 3.3 / (R192/(R191+R192)),))
            file.write("WAND: %4.3f\n" % (int.from_bytes(inaC_vbus, byteorder='big') * 0.00125))
        else:
            file.write("Type C eFUSE: OFF\n")
            file.write("+5V: %4.3f V\n" % ((values[1] / 1024) * 3.3 / (R192/(R191+R192)),))
            file.write("WAND: %4.3f V\n" % (int.from_bytes(inaC_vbus, byteorder='big') * 0.00125))
        file.write("INA_C Shunt: %4.3f mV\n" % (int.from_bytes(inaC_shnt, byteorder='big') * 0.0025))
        file.write("INA_C VBus: %4.3f V\n" % (int.from_bytes(inaC_vbus, byteorder='big') * 0.00125))
        file.write("INA_C Curr: %4.3f mA\n" % (int.from_bytes(inaC_curr, byteorder='big') * 0.15))
        file.write("INA_C Pwr: %4.3f mW\n" % (int.from_bytes(inaC_pwr, byteorder='big') * 2.5))
        file.write("\n")
    print("\nBye")
