import httpx

with httpx.Client() as client:
    with client.stream("GET", "https://httpbin.org/get") as response:
        network_stream = response.extensions["network_stream"]
        server_addr = network_stream.get_extra_info("server_addr")
        #  print(response.json())
        print(response.read().decode())
        print(server_addr)