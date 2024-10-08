# IP Basics

Setup is similar to [Ethernet Basics](./Ethernet_Basics.md), but uses IPDevice in order to enable the IP stack:

```
from networksim.hardware.device.infrastructure.switch import Switch
from networksim.hardware.device.ip.ipdevice import IPDevice
from networksim.ipaddr import IPAddr, IPNetwork
from networksim.simulation import Simulation


sim = Simulation()

A = IPDevice(name="A")
B = IPDevice(name="B")
C = IPDevice(name="C")

SW1 = Switch(name="SW1")
SW2 = Switch(name="SW2")

sim.add_device(A)
sim.add_device(B)
sim.add_device(C)
sim.add_device(SW1)
sim.add_device(SW2)

sim.connect_devices(SW1, SW2)
sim.connect_devices(A, SW1)
sim.connect_devices(B, SW1)
sim.connect_devices(C, SW2)
```

Using IP addressing comes with two new requirements. First, we must bind an IP address to a device interface, and then we must be able to map IP addresses of others to the hardware address on the LAN to send the packets to.

To bind an IP address to Device "A"'s interface:

```
A.ip.bind(IPAddr.from_str("192.168.1.5"), IPNetwork(IPAddr.from_str("192.168.1.0"), 24), A[0])
```

This will register this address and network in the IP stack to the interface on the device, and trigger the device to send a Gratuitous ARP, which is a broadcast message to other hosts on the same Ethernet segment to tell them the hardware address that the IP belongs to. When a device receives an ARP or IP packet from another device with an IP in a network it is bound to, it will keep track of it's hardware address within it's ARP table, similar to how a switch tracks the hardware address and interface mapping in it's CAM table.

If we step the simulation forward by 12 with `sim.step(12)` (so the GARP from A can reach Device B (8) that is on the same switch and Device C (12) attached to the other switch), we can see that both other Devices do not track this mapping yet using `sim.show()`:

```
DEVICES (queue in | queue out):
 * A:
   * Iface[0] (c0:db:77:20:c2:01): 0 | 0
     * 192.168.1.5/24
 * B:
   * Iface[0] (56:8e:0a:50:aa:01): 0 | 0
 * C:
   * Iface[0] (27:9a:e6:ca:44:01): 0 | 0
 * SW1:
   * Iface[0]: 0 | 0
   * Iface[1]: 0 | 0
   * Iface[2]: 0 | 0
   * Iface[3]: 0 | 0
 * SW2:
   * Iface[0]: 0 | 0
   * Iface[1]: 0 | 0
   * Iface[2]: 0 | 0
   * Iface[3]: 0 | 0
CABLES (a->b | b->a):
 * SW1[0]/SW2[0]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * A[0]/SW1[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * B[0]/SW1[2]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * C[0]/SW2[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
CAM TABLES:
 * SW1
   * Iface[0]: []
   * Iface[1]: ['c0:db:77:20:c2:01']
   * Iface[2]: []
   * Iface[3]: []
 * SW2
   * Iface[0]: ['c0:db:77:20:c2:01']
   * Iface[1]: []
   * Iface[2]: []
   * Iface[3]: []
ARP TABLES:
 * A
 * B
 * C
ROUTE TABLES:
 * A
   * 192.168.1.0/24 dev c0:db:77:20:c2:01 src 192.168.1.5
 * B
 * C
```

We can bind addresses to B and C to see how A behaves, with B in a different subnet and C with two addresses bound, one for each subnet:

```
B.ip.bind(IPAddr.from_str("192.168.0.10"), IPNetwork(IPAddr.from_str("192.168.0.0"), 24), B[0])
C.ip.bind(IPAddr.from_str("192.168.1.15"), IPNetwork(IPAddr.from_str("192.168.1.15"), 24), C[0])
C.ip.bind(IPAddr.from_str("192.168.0.20"), IPNetwork(IPAddr.from_str("192.168.0.20"), 24), C[0])
```

Then step the simulation forward 13 times with `sim.step(13)` (for the extra packet queued from C), and we can see how the ARP tables and IP address binds look:

```
DEVICES (queue in | queue out):
 * A:
   * Iface[0] (c0:db:77:20:c2:01): 0 | 0
     * 192.168.1.5/24
 * B:
   * Iface[0] (56:8e:0a:50:aa:01): 0 | 0
     * 192.168.0.10/24
 * C:
   * Iface[0] (27:9a:e6:ca:44:01): 0 | 0
     * 192.168.1.15/24
     * 192.168.0.20/24
 * SW1:
   * Iface[0]: 0 | 0
   * Iface[1]: 0 | 0
   * Iface[2]: 0 | 0
   * Iface[3]: 0 | 0
 * SW2:
   * Iface[0]: 0 | 0
   * Iface[1]: 0 | 0
   * Iface[2]: 0 | 0
   * Iface[3]: 0 | 0
CABLES (a->b | b->a):
 * SW1[0]/SW2[0]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * A[0]/SW1[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * B[0]/SW1[2]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * C[0]/SW2[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
CAM TABLES:
 * SW1
   * Iface[0]: ['27:9a:e6:ca:44:01']
   * Iface[1]: ['c0:db:77:20:c2:01']
   * Iface[2]: ['56:8e:0a:50:aa:01']
   * Iface[3]: []
 * SW2
   * Iface[0]: ['c0:db:77:20:c2:01', '56:8e:0a:50:aa:01']
   * Iface[1]: ['27:9a:e6:ca:44:01']
   * Iface[2]: []
   * Iface[3]: []
ARP TABLES:
 * A
   * 192.168.1.15: 27:9a:e6:ca:44:01
 * B
   * 192.168.0.20: 27:9a:e6:ca:44:01
 * C
   * 192.168.0.10: 56:8e:0a:50:aa:01
ROUTE TABLES:
 * A
   * 192.168.1.0/24 dev c0:db:77:20:c2:01 src 192.168.1.5
 * B
   * 192.168.0.0/24 dev 56:8e:0a:50:aa:01 src 192.168.0.10
 * C
   * 192.168.1.0/24 dev 27:9a:e6:ca:44:01 src 192.168.1.15
   * 192.168.0.0/24 dev 27:9a:e6:ca:44:01 src 192.168.0.20
```

It is important to note that while A knows about C now, C does not know about A, even though it has an address in the same subnet as one of C's bound addresses. This is because C received the GARP from A before it bound it's IP to the interface. Both B and C know each other's addresses, as they bound their IP addresses before they received each other's GARP broadcasts.

C can either wait to receive another GARP from A, or any IP packet from A, or C can query the network and ask for the owner of the IP address, if it was wanting to send an IP packet. To query the network for "192.168.1.5", C can send an ARP Request in order to generate an ARP Reply from A. This packet will be broadcast to all devices on the same Ethernet segment:

```
C.ip.send_arp_request(IPAddr.from_str("192.168.1.5"))
```

After stepping the simulation 24 times (12 for the request to reach A, 12 more for the response back to C):

```
DEVICES (queue in | queue out):
 * A:
   * Iface[0] (c0:db:77:20:c2:01): 0 | 0
     * 192.168.1.5/24
 * B:
   * Iface[0] (56:8e:0a:50:aa:01): 0 | 0
     * 192.168.0.10/24
 * C:
   * Iface[0] (27:9a:e6:ca:44:01): 0 | 0
     * 192.168.1.15/24
     * 192.168.0.20/24
 * SW1:
   * Iface[0]: 0 | 0
   * Iface[1]: 0 | 0
   * Iface[2]: 0 | 0
   * Iface[3]: 0 | 0
 * SW2:
   * Iface[0]: 0 | 0
   * Iface[1]: 0 | 0
   * Iface[2]: 0 | 0
   * Iface[3]: 0 | 0
CABLES (a->b | b->a):
 * SW1[0]/SW2[0]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * A[0]/SW1[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * B[0]/SW1[2]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * C[0]/SW2[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
CAM TABLES:
 * SW1
   * Iface[0]: ['27:9a:e6:ca:44:01']
   * Iface[1]: ['c0:db:77:20:c2:01']
   * Iface[2]: ['56:8e:0a:50:aa:01']
   * Iface[3]: []
 * SW2
   * Iface[0]: ['c0:db:77:20:c2:01', '56:8e:0a:50:aa:01']
   * Iface[1]: ['27:9a:e6:ca:44:01']
   * Iface[2]: []
   * Iface[3]: []
ARP TABLES:
 * A
   * 192.168.1.15: 27:9a:e6:ca:44:01
 * B
   * 192.168.0.20: 27:9a:e6:ca:44:01
 * C
   * 192.168.0.10: 56:8e:0a:50:aa:01
   * 192.168.1.5: c0:db:77:20:c2:01
ROUTE TABLES:
 * A
   * 192.168.1.0/24 dev c0:db:77:20:c2:01 src 192.168.1.5
 * B
   * 192.168.0.0/24 dev 56:8e:0a:50:aa:01 src 192.168.0.10
 * C
   * 192.168.1.0/24 dev 27:9a:e6:ca:44:01 src 192.168.1.15
   * 192.168.0.0/24 dev 27:9a:e6:ca:44:01 src 192.168.0.20
```

We can do some simple Ping tests using the ping application to send ICMP Echo Request packets and handle ICMP Echo Reply packets:

```
from networksim.application.ping import Ping

A.add_application(Ping, "ping")
A.start_application("ping", IPAddr.from_str("192.168.1.15"))
```

And stepping through the simulation for a bit (for example, 100 times), we can check the process log:

```
A.process_list[1].log
```

...and see the following:

```
['1: Sending Ping with seq=1',
 '24: 192.168.1.5 recieved PONG from 192.168.1.15 seq=1: 24',
 '25: Sending Ping with seq=2',
 '49: 192.168.1.5 recieved PONG from 192.168.1.15 seq=2: 24',
 '50: Sending Ping with seq=3',
 '74: 192.168.1.5 recieved PONG from 192.168.1.15 seq=3: 24',
 '75: Sending Ping with seq=4',
 '99: 192.168.1.5 recieved PONG from 192.168.1.15 seq=4: 24',
 '100: Sending Ping with seq=5',
```

This application will also send an ARP request if the host is not already known. If we stop the Ping (`A.stop_application(1)`) then step the simulation forward enough for the ARP table entries to expire, we can then start another Ping as before, and check it's logs (note, the process ID will now be 2, instead of 1, as this ID always increments) and step the simulation forward again to see the result in the logs:

```
['1: Host unknown, sending ARP',
 '26: Sending Ping with seq=1',
 '50: 192.168.1.5 recieved PONG from 192.168.1.15 seq=1: 24',
 '51: Sending Ping with seq=2',
 '75: 192.168.1.5 recieved PONG from 192.168.1.15 seq=2: 24',
 '76: Sending Ping with seq=3',
 '100: 192.168.1.5 recieved PONG from 192.168.1.15 seq=3: 24']
```

## DHCP
Instead of assigning static IP addresses, DHCP can be used. One device must have a static IP address to act as the DHCP server. The DHCP Server application can be started with:

```
from networksim.application.dhcp.server import DHCPServer

dhcp_server.add_application(DHCPServer, "dhcp_server")
dhcp_server.start_application(
    "dhcp_server",
    network=dhcp_server.ip.bound_ips.get_binds(
        iface=dhcp_server[0],
    )[0].network,
)
```

This server will start responding to DHCP requests from clients on the network, which can then be started with the following for each device:

```
from networksim.application.dhcp.client import DHCPClient

A.add_application(DHCPClient, "dhcp_client")
A.start_application("dhcp_client")
```

This will start the DHCP Client for every interface on the device (alternatively, a list of interfaces can be passed when starting the application if only specific interfaces are desired for DHCP). For each connected interface, the DHCP Client will start sending DHCPDiscover messages and begin the process of getting an IP address from the DHCP Server, which is a 2-step process, with each step being a query from the client and a reply from the server (DHCPDiscover->DHCPOffer, DHCPRequest->DHCPAck), at which point the client will bind the issued IP to the interface, and periodically renew it based on the renewal, rebind, and expiration times.
