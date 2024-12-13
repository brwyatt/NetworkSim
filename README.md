# NetworkSim
Educational Network Simulation Tool

![](docs/assets/header.gif)

## Overview
This project was started as a way to both learn and teach how networks work at the protocol level in a human-friendly time scale. As such, there are some "interesting" deviations from reality, particularly the "physical" layer and time, it is a _simulation_, after all. No code in here should be considered "production quality", and should be expected to contain vulnerabilities that have been patched in real-world implementations (but these could be fun to "exploit" in the simulation).

## Installing

```
python3 -m venv networksim
source networksim/bin/activate
pip install git+https://github.com/brwyatt/NetworkSim.git#egg=networksim
```

## Basic Usage (GUI)

The GUI can be launched (after install, within the virtual env) with `networksim`. This will launch a blank simulation environment.

Devices can be added to the simulation from the panel on the left, and are grouped into collapsable sections.

![](docs/assets/device_panel.png)

The panel at the bottom contain the simulation contols and show the current step count of the simulation and controls for moving the simulation forward, as well as a button to reset the view pane.

![](docs/assets/sim_controls.png)

Clicking on a device type on the left panel will open a device creation window, where default options can be changed or optional information can be provided. For example, this can be used to change the number and properties of interfaces a device has, its name, and how fast it is able to process packets.

![](docs/assets/device_create.png)

Once there are two more more devices (for example, a device and a switch), they can be connected by right-clicking one of them, selecting an interface from the interface menu, and clicking the "Connect" option to enter connection mode.

![](docs/assets/device_connect_a.png)

When in connection mode, click another device to select one of it's available interfaces to connect to.

![](docs/assets/device_connect_b.png)

A cable creation dialog window will open where you can change the characteristics of the cable.

![](docs/assets/cable_create.png)

Note that the connection between devices will use the smallest properties of the connected interfaces AND the cable. If the interfaces on the devices have a bandwidth of 10, but the cable only has a bandwidth of 1, the connection will be limited to a bandwidth of 1.
The "length" determines how many "steps" in the simulation it takes packets to travel between interfaces.

Once connected, packets can be sent via the interface menu, and packets traveling along a cable can be clicked on to inspect their contents. Devices can also be disconnected by right-clicking the cable connecting them and clicking "delete".

## Advanced Usage (Python)

Note: This section is intended to be used as a quick "how to use the simulator in Python", and will be light on explaining networking concepts.

Start by either running Python interactively or (preferred) installing and running iPython to get an interactive shell to run the simulation.

The `Simulation` object is what controls all simulation activity.

```
from networksim.simulation import Simulation

sim = Simulation()
```

We can progress the simulation's time with the `step()` function, which takes an optional integer parameter for number of steps (default is 1).

```
sim.setp(20)
```

But this doesn't do much at present, as we don't have any devices in the simulaton or any packets. We can add a couple Ethernet `Device`s (devices that can only speak the low-level Ethernet protocol) and a `Switch` (a networking device that moves packets within a network based on low-level Ethernet addresses) to the simulation

```
from networksim.hardware.device import Device
from networksim.hardware.device.infrastructure.switch import Switch

A = Device(name="A")
B = Device(name="B")
SW = Switch(name="SW")

sim.add_device(A)
sim.add_device(B)
sim.add_device(SW)
```

By default, `Device`s have a single interface, and `Switch`es have 4. You can see the current state of the simulation, and see that the devices have been added with the `show()` function, which will output all devices and their interfaces (including their hardware ("MAC") addresses), as well as their in/out queue sizes.

```
sim.show()
```

They aren't connected yet, however, we need to connect them, which we can do two ways:

Manually creating a cable, connecting it to the device interface, and adding it to the simulation:
```
from networksim.hardware.cable import Cable

cable_A_SW = Cable(A[0], SW[0])
sim.add_cable(cable_A_SW)
```

Having the simulation create the cable and connect to the first available (unused) interface on a device for you (which will, additionally, add the devices to the simulation if they aren't already):
```
sim.connect_devices(B, SW)
```

After that, both devices should be connected to the switch. Both methods, by default, will create cables of length 3 with a bandwidth of 1. You can check the new state with `sim.show()` and see the cables connecting the devices to the switch, as well as see any packets traveling along the cables (which should be none).

Now that we have both devices connected to the switch, they should be able to send Ethernet packets to each other. We can send a packet from A to B with the following:

```
A[0].send(EthernetPacket(dst=B[0].hwid, payload="Hello B!"))
```

And a `sim.show()` will show that Iface[0] on device A has a packet on the outbound queue. If we advance the simulation by 1 (`sim.step()`), we can see the packet on the cable between A and the switch by running `show()` again.

If we advance the simulation 3 more times (`sim.step(3)`), we can see a packet on the outbound queue of Iface[1] of SW. As well as an entry for A's hardware address in the switch's CAM table (more on that later).

Advancing the simulation 4 more steps will show a packet on the inbound queue for B. Unlike `Switch`es (and, later, `IPDevice`s), basic Ethernet `Device`s don't automatically process packets from their queue by default. But we can manually read the packet from the interface ourselves.

```
B[0].receive().payload
```

The list of all devices in the simulation can be accessed with:

```
sim.devices
```

### Loading examples

Examples from the examples directory are JSON (.nsj) or gzip-compressed JSON (.nsj.gz) data files and can be read using the `gzip` and `json` libraries, then de-serialized by passing the resulting dictionary to `Simulation.deserialize(data)`.

For example:

```python
import gzip
import json

from networksim.simulation import Simulation


file_path = "./examples/SimpleRoutedNetwork.nsj"

with open(file_path, "rb") as file:
    data = file.read()

if file_path.endswith(".gz"):
    data = gzip.decompress(data)
data = json.loads(data.decode())

sim = Simulation.deserialize(data)
```

## Tutorials/Lessons
(These are still a WIP)
* [Ethernet Basics](./docs/Ethernet_Basics.md)
* [IP Basics](./docs/IP_Basics.md)
* [Routing Basics](./docs/Routing_Basics.md)

## Example networks
### Tier-3 Network
File: `./examples/Tier3Network.nsj`

Creates a Core switch, 2 Aggregation switches connected to the core, 4 Access switches split between the Aggregation switches, a DHCP server (connected to an Aggregation switch with increased bandwidth), and 50 clients randomly connected to the Access switches.

```
              Core
              /  \
         -----    ------
        |               |
      Agg1 - DHCP     Agg2
      /  \            /  \
  Acc1    Acc2    Acc3    Acc4
 / | \   / | \   / | \   / | \
A  B  C D  E  F G  H  I J  K  L
```

### Routing

File: `./examples/SimpleRouting.nsj`

Creates two networks connected with a router. Each network has a switch, a DHCP server, and 5 clients.

```
         Router
        /      \
     SW1        SW2
    / | \      / | \
DHCP  A1 A2  B1 B2  DHCP
```

## Limitations (Deviations from reality)
* The time units analogue in the simulation are "steps".
  * Cable lengths are measured in the number of "steps" for packets to taverse the length of the cable
  * Interface buffers are based on the number of "steps" worth of packets that can be stored (relative to their bandwidth)
* Cables (Physical layer oddities)
  * These decisions were made in order to make it easy to simulate/control and keep the focus on the higher level protocols, and the actual implementation here actually doesn't matter, as the protocols are intended to be run over different physical layers, and do in the real world (2- or 4-pair copper CAT cables, Multi-/Single-Mode fiber, and encapsulated protocols such as GPON (fiber internet), DOCSIS (cable internet), and VPN)
  * Unlike the real world, packets "exist" on the cable in discrete units (rather than conducting electical signals between ends)
  * Cables are "active" in that they are actually the entity in the simulation pulling packets off of interface outbound buffers and placing them on interface inbound buffers, rather than just being a conduit for electrical signals or light transmitted from the interface and received on the other end.
  * the "bandwidth" is the number of packets per "step" along the cable. This would be most analagous to the higher frequency of CAT cables that higher-rated cables (and interfaces) use to achieve higher bandwidth.
* Packets are the fundamental unit
  * Unlike the real world, packets are transmitted as a single discrete unit, irrelevant of size.
  * Packets are also structured Python objects, for ease of inspection and exploration/understanding of protocols, rather than being raw binary data. The idea is to teach "IP Packets are encapsulated in an Ethernet packet have a source and destination IP address" rather than "these x bytes of the IP data frame portion of the packet contains y data".
* Device packet processing
  * By default, devices are configured to be able to read the combined bandwidth of all interfaces every step. This will, by default, ensure the inbound buffers can never fill. This can be tweaked to slow the processing of packets to allow for "overwhelming" a host and dropping packets.
    * On switches, this default can easily lead to overflowing of outbound buffers on popular destination interfaces, unless those are manually increased.
    * For simplicity, "applications" listening on a host, can process and respond to a packet (or multiple packets) within the same step, without any kind of time delay for processing like the real world would normally see.

## TODO
Known missing things that might get implemented

* ICMP Error messages - Currently missing, both generating/sending and processing received errors
* TCP - Requires a bit more tracking, still making sure the basics are all worked out
* VLANs - May require some rework of some parts to support, but likely worth implementing as the concepts are pretty useful
* (R)STP - Might be out of scope. Lets be honest, though, if you know what this is, this really isn't for you anyway. 😉
* Interface bonding and LACP - might be fun, might also be out of scope (at least short-term)
