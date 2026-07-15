from xmlrpc.client import ServerProxy
import sys

def main():
    # Connect directly to the loopback IP address
    server_url = "http://127.0.0.1:8888"
    print(f"Connecting to server at {server_url}...")

    with ServerProxy(server_url) as proxy:
        # if power adc on
        if len(sys.argv) == 2 and sys.argv[1] == 'on':
            adc_result = proxy.on()
            print(f"ADC Power: {adc_result}")
        elif len(sys.argv) == 2 and sys.argv[1] == 'rst':
            adc_result = proxy.rst()
            print(f"FX3 Reset: {adc_result}")
        else:
            adc_result = proxy.off()
            print(f"ADC Power: {adc_result}")

if __name__ == "__main__":
    main()
