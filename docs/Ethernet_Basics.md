# Ethernet Basics
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

This creates a simple network with 3 devices with 1 interface each and 2 switches with 4 interfaces. All interfaces will get randomized hardware IDs. The switches are connected to each other with cables of length 3 (measured in simulation steps), the first two devices are on the first switch, and the 3rd device is on the second switch.

Essentially, it looks like this:

```
   SW1 -- SW2
   / \     |
  A   B    C
```

The simulation does not progress unless `sim.step()` is called. When the simulation progresses, each cable will place packets at the end of the cable's lenth onto the corresponding destination interface's inbound queue, then progress remainling packets along the cable's distance by 1, then will read one packetfrom the outbound queues of the connected interfaces to the start of the cable's length. Next each switch will read from each of it's interface's inbound queues, and forward the 1 packet to the outbound queue of the destination interface (or interfaces, if the hardware ID is not found in the CAM table).

The current state of all packets and devices can be viewed with `sim.show()`. This will show the status (size) of the inbound and outbound queues of all interfaces on all devices, the status of all packets traveling along cables, and the contents of the CAM tables on all switches.

For example:
```
DEVICES (queue in | queue out):
 * A:
   * Iface[0] (c6:ad:c9:ba:60:01): 0 | 0
 * B:
   * Iface[0] (88:76:b9:9a:1e:01): 0 | 0
 * C:
   * Iface[0] (8c:5c:af:15:94:01): 0 | 0
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
 * SW1[0]/SW2[0]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * A[0]/SW1[1]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * B[0]/SW1[2]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * C[0]/SW2[1]: ['None', 'None', 'None'] | ['None', 'None', 'None']
CAM TABLES:
 * SW1
   * Iface[0]: []
   * Iface[1]: []
   * Iface[2]: []
   * Iface[3]: []
 * SW2
   * Iface[0]: []
   * Iface[1]: []
   * Iface[2]: []
   * Iface[3]: []
ARP TABLES:
ROUTE TABLES:
```

A packet can be sent from A to B by placing it on the outbound queue of A's interface and giving it a destination of B's interface hardware ID. This can be done by calling either `outbound_write(packet)` or the more convenient `send(packet)`. For example:

```
A[0].send(EthernetPacket(dst=B[0].hwid, payload="TEST A->B"))
```

After advancing the state of the simulation 8 steps (1 for it to go from the outbound queue to the cable, 2 to traverse the cable, 1 more to go from the cable to the switch, which processes it from the inbound queue to the outbound queues to B and the other switch (assuming B is not in the CAM tables), then 1 more to get placed on the cable to B, 2 to traverse the cable, and 1 more to get to B's inbound queue) the packet can be read from the interface on B with `inbound_read()` or the more convenient `receive()`. For example:

```
str(B[0].receive())
```

After sending packets from all devices, the state will look something like this:

```
DEVICES (queue in | queue out):
 * A:
   * Iface[0] (c6:ad:c9:ba:60:01): 1 | 0
 * B:
   * Iface[0] (88:76:b9:9a:1e:01): 1 | 0
 * C:
   * Iface[0] (8c:5c:af:15:94:01): 3 | 0
 * SW1:
   * Iface[0]: 0 | 0
   * Iface[1]: 0 | 0
   * Iface[2]: 0 | 0
   * Iface[3]: 0 | 0
 * SW2:
   * Iface[0]: 0 | 0
   * Iface[1]: 0 | 1
   * Iface[2]: 0 | 0
   * Iface[3]: 0 | 0
CABLES (a->b | b->a):
 * SW1[0]/SW2[0]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * A[0]/SW1[1]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * B[0]/SW1[2]: ['None', 'None', 'None'] | ['None', 'None', 'None']
 * C[0]/SW2[1]: ['None', 'None', 'None'] | ['None', 'None', 'None']
CAM TABLES:
 * SW1
   * Iface[0]: ['8c:5c:af:15:94:01']
   * Iface[1]: ['c6:ad:c9:ba:60:01']
   * Iface[2]: ['88:76:b9:9a:1e:01']
   * Iface[3]: []
 * SW2
   * Iface[0]: ['c6:ad:c9:ba:60:01', '88:76:b9:9a:1e:01']
   * Iface[1]: ['8c:5c:af:15:94:01']
   * Iface[2]: []
   * Iface[3]: []
ARP TABLES:
ROUTE TABLES:
```
