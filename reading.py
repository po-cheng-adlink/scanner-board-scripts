from xmlrpc.client import ServerProxy

def main():
    # Connect directly to the loopback IP address
    server_url = "http://127.0.0.1:8888"
    print(f"Connecting to server at {server_url}...")

    with ServerProxy(server_url) as proxy:
        # Call the registered 'read' function
        adc_result = proxy.read()
        print(f"{adc_result}")

if __name__ == "__main__":
    main()
