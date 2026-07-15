import EasyMCP2221
import sys
import time

mcp = EasyMCP2221.Device()
mcp.I2C_write(0x20, b'\x03\xFD')
ioext = None

loop = 0
while True:
    loop += 1
    try:
        ioext = mcp.I2C_Slave(0x20)
    except RuntimeError:
        if loop > 4:
            raise RuntimeError("Unable to get I2c slaves")
        mcp.I2C_speed((100000*loop))
        time.sleep(1)
        continue
    else:
        break

try:
    if ioext.is_present():
        regval = ioext.read_register(0x00, 1)
        print(f"ioext: {regval}")
        if len(sys.argv) == 2:
            if sys.argv[1] == "on" or sys.argv[1] == "trg":
               trgval = bytes(a & b for a, b in zip(regval, b'\xFD'))
               ioext.write_register(0x01, trgval)
               time.sleep(1)
               print(f"=> {trgval}")
            if sys.argv[1] == "off" or sys.argv[1] == "trg":
               rstval = bytes(a | b for a, b in zip(regval, b'\x02'))
               ioext.write_register(0x01, rstval)
               print(f"=> {rstval}")

except EasyMCP2221.exceptions.NotAckError:
    pass
