import EasyMCP2221

mcp=EasyMCP2221.Device()
mcp.set_pin_function(gp0="GPIO_OUT", gp1="ADC", gp2="ADC", gp3="ADC")
mcp.GPIO_write(gp0 = True)
mcp.ADC_config(ref="VDD")
