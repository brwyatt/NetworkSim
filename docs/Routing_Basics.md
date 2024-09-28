# Routing Basics
Ethernet works well for things that are relatively nearby, and can also be noisy when switches flood their ports when a Hardware address is unknown, as this propagates through all switches on the network. IP networking allows us to break up these networks into logical groups, called "subnets". These subnets, if connected to other networks, can define a default address to handle traffic for addresses not part of the local subnet, this is called a "router".

This default address is reffered to as the "default route" and is often notated as the "0.0.0.0/0" network which will match any destination that doesn't match another network route (such as "192.168.0.1/24") that is more specific/narrow. This can be manually defined (in the case of a static IP network) or provided by the DHCP server.

Lets start by creating two separate networks, one with static IPs, one using DHCP:

```
from networksim.application.dhcp.client import DHCPClient
from networksim.application.dhcp.server import DHCPServer
from networksim.hardware.device.infrastructure.switch import Switch
from networksim.hardware.device.ip.ipdevice import IPDevice
from networksim.ipaddr import IPAddr
from networksim.ipaddr import IPNetwork
from networksim.simulation import Simulation


sim = Simulation()

# Network 1
SW1 = Switch(name="SW1")
network_1 = IPNetwork(IPAddr.from_str("192.168.0.0"))

A = IPDevice(name="A")
sim.connect_devices(A, SW1)
A.ip.bind(IPAddr.from_str("192.168.0.10"), network_1, A[0])

# Network 2
SW2 = Switch(name="SW2")
network_2 = IPNetwork(IPAddr.from_str("172.16.20.0"))

DHCP_2 = IPDevice(name="DHCP_2")
sim.connect_devices(DHCP_2, SW2)
DHCP_2.ip.bind(IPAddr.from_str("172.16.20.5"), network_2, DHCP_2[0])
DHCP_2.add_application(DHCPServer, "dhcp_server")

B = IPDevice(name="B")
sim.connect_devices(B, SW2)
B.add_application(DHCPClient, "dhcp_client")
B.start_application("dhcp_client")
```

Now we have two networks, but they're not connected:

```
SW1  SW2
 |    | \
 A    B  DHCP_2
```

Note, we haven't started the DHCP server yet, as we some additional information we won't have until we add the router. So lets add the router:

```
from networksim.hardware.device.ip.router import Router

router = Router(name="router")
sim.connect_devices(router, SW1)
router.ip.bind(IPAddr.from_str("192.168.0.1"), network_1, router[0])
sim.connect_devices(router, SW2)
router.ip.bind(IPAddr.from_str("172.16.20.1"), network_2, router[1])
```

And now that we know the Router's IP address, we can configure and start the DHCP server:

```
DHCP_2.start_application(
    "dhcp_server",
    network=network_2,
    router=IPAddr.from_str("172.16.20.1"),
)
```

If we check the simulation state now (`sim.show()`), and check the route tables, we can see that A has a route for it's local network, the DHCP server has a route for it's local network, the router has routes for BOTH networks, and B has none, as we haven't stepped the simulation for it to get it's configuration from the DHCP server. So do that now.

```
sim.step(34)
```

And now we can see that B has 2 routes, one for it's local network, and another default route pointing to the router's IP on it's local subnet. But notice that A does not have a default route. This means that B can send IP packets to A, but A doesn't know where to send packets to B. We can see this by trying to ping from B to A:

```
from networksim.application.ping import Ping

B.add_application(Ping, "ping")
B.start_application("ping", IPAddr.from_str("192.168.0.10"))
```

And if we step through the simulation, leaving time for B to ARP for the router's hardware address, as it doesn't know it yet:

```
sim.step(17)  # ARP reply/response time
sim.step(8)  # Time for packet to reach the router
```

We can now see there is a packet on the outbound queue for the router's port connected to A's network. If we step through again, we can see it traversing the path to A (`sim.step(4)` will show the packet on the outbound queue for the port A is connected to on the switch), and that A does not respond (an error will print saying "No route to 172.16.20.X!").

And now, if we step the simulation through a bit more, and look at the ping application logs on B, we can see the timeouts.

```
sim.step(500)
B.process_list[2].log
```

To resolve this, we just need to tell A to use the router for traffic off it's local network:

```
A.ip.routes.add_route(
    IPNetwork(addr=IPAddr(byte_value=bytes(IPAddr.length_bytes)), match_bits=0),
    port=A[0],
    via=IPAddr.from_str("192.168.0.1"),
)
```

And we can see with `sim.show()` that it has a default route, similar to B, but pointing to the IP of the router on it's own network. And if we step the simulation forward again, we can see B starts to receive replies.

```
sim.step(500)
B.process_list[2].log
```
