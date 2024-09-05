# NetworkSim
Educational Network Simulation Tool

## Basic Usage (Ethernet)
Example setup of a simulation:

```
from networksim.hardware.device import Device
from networksim.hardware.device.infrastructure.switch import Switch
from networksim.packet.ethernet import EthernetPacket
from networksim.simulation import Simulation


sim = Simulation()

A = Device(name="A")
B = Device(name="B")
C = Device(name="C")

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

This creates a simple network with 3 devices with 1 port each and 2 switches with 4 ports. All ports will get randomized hardware IDs. The switches are connected to each other with cables of length 3 (measured in simulation steps), the first two devices are on the first switch, and the 3rd device is on the second switch.

Essentially, it looks like this:

```
   SW1 -- SW2
   / \     |
  A   B    C
```

The simulation does not progress unless `sim.step()` is called. When the simulation progresses, each cable will place packets at the end of the cable's lenth onto the corresponding destination port's inbound queue, then progress remainling packets along the cable's distance by 1, then will read one packetfrom the outbound queues of the connected ports to the start of the cable's length. Next each switch will read from each of it's port's inbound queues, and forward the 1 packet to the outbound queue of the destination port (or ports, if the hardware ID is not found in the CAM table).

The current state of all packets and devices can be viewed with `sim.show()`. This will show the status (size) of the inbound and outbound queues of all ports on all devices, the status of all packets traveling along cables, and the contents of the CAM tables on all switches.

For example:
```
DEVICES (queue in | queue out):
 * A:
   * Port[0] (c6:ad:c9:ba:60:01): 0 | 0
 * B:
   * Port[0] (88:76:b9:9a:1e:01): 0 | 0
 * C:
   * Port[0] (8c:5c:af:15:94:01): 0 | 0
 * SW1:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 0
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
 * SW2:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 0
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
CABLES (a->b | b->a):
 * SW1[0]/SW2[0]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * A[0]/SW1[1]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * B[0]/SW1[2]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * C[0]/SW2[1]: ['None', 'None', 'None'] | ['None', 'None', 'None']
CAM TABLES:
 * SW1
   * Port[0]: []
   * Port[1]: []
   * Port[2]: []
   * Port[3]: []
 * SW2
   * Port[0]: []
   * Port[1]: []
   * Port[2]: []
   * Port[3]: []
ARP TABLES:
ROUTE TABLES:
```

A packet can be sent from A to B by placing it on the outbound queue of A's port and giving it a destination of B's port hardware ID. This can be done by calling either `outbound_write(packet)` or the more convenient `send(packet)`. For example:

```
A[0].send(EthernetPacket(dst=B[0].hwid, payload="TEST A->B"))
```

After advancing the state of the simulation 8 steps (1 for it to go from the outbound queue to the cable, 2 to traverse the cable, 1 more to go from the cable to the switch, which processes it from the inbound queue to the outbound queues to B and the other switch (assuming B is not in the CAM tables), then 1 more to get placed on the cable to B, 2 to traverse the cable, and 1 more to get to B's inbound queue) the packet can be read from the port on B with `inbound_read()` or the more convenient `receive()`. For example:

```
str(B[0].receive())
```

After sending packets from all devices, the state will look something like this:

```
DEVICES (queue in | queue out):
 * A:
   * Port[0] (c6:ad:c9:ba:60:01): 1 | 0
 * B:
   * Port[0] (88:76:b9:9a:1e:01): 1 | 0
 * C:
   * Port[0] (8c:5c:af:15:94:01): 3 | 0
 * SW1:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 0
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
 * SW2:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 1
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
CABLES (a->b | b->a):
 * SW1[0]/SW2[0]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * A[0]/SW1[1]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * B[0]/SW1[2]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * C[0]/SW2[1]: ['None', 'None', 'None'] | ['None', 'None', 'None']
CAM TABLES:
 * SW1
   * Port 0: ['8c:5c:af:15:94:01']
   * Port 1: ['c6:ad:c9:ba:60:01']
   * Port 2: ['88:76:b9:9a:1e:01']
   * Port 3: []
 * SW2
   * Port 0: ['c6:ad:c9:ba:60:01', '88:76:b9:9a:1e:01']
   * Port 1: ['8c:5c:af:15:94:01']
   * Port 2: []
   * Port 3: []
ARP TABLES:
ROUTE TABLES:
```

## Using IP protocols

Setup is similar, but uses IPDevice in order to enable the IP stack:

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

Using IP addressing comes with two new requirements. First, we must bind an IP address to a device port, and then we must be able to map IP addresses of others to the hardware address on the LAN to send the packets to.

To bind an IP address to Device "A"'s port:

```
A.ip.bind(IPAddr.from_str("192.168.1.5"), IPNetwork(IPAddr.from_str("192.168.1.0"), 24), A[0])
```

This will register this address and network in the IP stack to the port on the device, and trigger the device to send a Gratuitous ARP, which is a broadcast message to other hosts on the same Ethernet segment to tell them the hardware address that the IP belongs to. When a device receives an ARP or IP packet from another device with an IP in a network it is bound to, it will keep track of it's hardware address within it's ARP table, similar to how a switch tracks the hardware address and port mapping in it's CAM table.

If we step the simulation forward by 12 with `sim.step(12)` (so the GARP from A can reach Device B (8) that is on the same switch and Device C (12) attached to the other switch), we can see that both other Devices do not track this mapping yet using `sim.show()`:

```
DEVICES (queue in | queue out):
 * A:
   * Port[0] (c0:db:77:20:c2:01): 0 | 0
     * 192.168.1.5/24
 * B:
   * Port[0] (56:8e:0a:50:aa:01): 0 | 0
 * C:
   * Port[0] (27:9a:e6:ca:44:01): 0 | 0
 * SW1:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 0
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
 * SW2:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 0
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
CABLES (a->b | b->a):
 * SW1[0]/SW2[0]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * A[0]/SW1[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * B[0]/SW1[2]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * C[0]/SW2[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
CAM TABLES:
 * SW1
   * Port[0]: []
   * Port[1]: ['c0:db:77:20:c2:01']
   * Port[2]: []
   * Port[3]: []
 * SW2
   * Port[0]: ['c0:db:77:20:c2:01']
   * Port[1]: []
   * Port[2]: []
   * Port[3]: []
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
   * Port[0] (c0:db:77:20:c2:01): 0 | 0
     * 192.168.1.5/24
 * B:
   * Port[0] (56:8e:0a:50:aa:01): 0 | 0
     * 192.168.0.10/24
 * C:
   * Port[0] (27:9a:e6:ca:44:01): 0 | 0
     * 192.168.1.15/24
     * 192.168.0.20/24
 * SW1:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 0
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
 * SW2:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 0
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
CABLES (a->b | b->a):
 * SW1[0]/SW2[0]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * A[0]/SW1[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * B[0]/SW1[2]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * C[0]/SW2[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
CAM TABLES:
 * SW1
   * Port[0]: ['27:9a:e6:ca:44:01']
   * Port[1]: ['c0:db:77:20:c2:01']
   * Port[2]: ['56:8e:0a:50:aa:01']
   * Port[3]: []
 * SW2
   * Port[0]: ['c0:db:77:20:c2:01', '56:8e:0a:50:aa:01']
   * Port[1]: ['27:9a:e6:ca:44:01']
   * Port[2]: []
   * Port[3]: []
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
   * Port[0] (c0:db:77:20:c2:01): 0 | 0
     * 192.168.1.5/24
 * B:
   * Port[0] (56:8e:0a:50:aa:01): 0 | 0
     * 192.168.0.10/24
 * C:
   * Port[0] (27:9a:e6:ca:44:01): 0 | 0
     * 192.168.1.15/24
     * 192.168.0.20/24
 * SW1:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 0
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
 * SW2:
   * Port[0]: 0 | 0
   * Port[1]: 0 | 0
   * Port[2]: 0 | 0
   * Port[3]: 0 | 0
CABLES (a->b | b->a):
 * SW1[0]/SW2[0]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * A[0]/SW1[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * B[0]/SW1[2]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
 * C[0]/SW2[1]: ['(None,)', '(None,)', '(None,)'] | ['(None,)', '(None,)', '(None,)']
CAM TABLES:
 * SW1
   * Port[0]: ['27:9a:e6:ca:44:01']
   * Port[1]: ['c0:db:77:20:c2:01']
   * Port[2]: ['56:8e:0a:50:aa:01']
   * Port[3]: []
 * SW2
   * Port[0]: ['c0:db:77:20:c2:01', '56:8e:0a:50:aa:01']
   * Port[1]: ['27:9a:e6:ca:44:01']
   * Port[2]: []
   * Port[3]: []
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
