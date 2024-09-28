# NetworkSim
Educational Network Simulation Tool

## Overview
This project was started as a way to both learn and teach how networks work at the protocol level. As such, there are some "interesting" deviations from reality, particularly on the "physical" layer and time, it is a _simulation_, after all. No code in here should be considered "production quality", and should be expected to contain vulnerabilities that have been patched in real-world implementations (but these could be fun to "exploit" in the simulation).

## Limitations (Deviations from reality)
* The time units analogue in the simulation are "steps".
  * Cable lengths are measured in the number of "steps" for packets to taverse the length of the cable
  * Port buffers are based on the number of "steps" worth of packets that can be stored (relative to their bandwidth)
* Cables (Physical layer oddities)
  * These decisions were made in order to make it easy to simulate/control and keep the focus on the higher level protocols, and the actual implementation here actually doesn't matter, as the protocols are intended to be run over different physical layers, and do in the real world (2- or 4-pair copper CAT cables, Multi-/Single-Mode fiber, and encapsulated protocols such as GPON (fiber internet), DOCSIS (cable internet), and VPN)
  * Unlike the real world, packets "exist" on the cable in discrete units (rather than conducting electical signals between ends)
  * Cables are "active" in that they are actually the entity in the simulation pulling packets off of port outbound buffers and placing them on port inbound buffers, rather than just being a conduit for electrical signals or light transmitted from the port and received on the other end.
  * the "bandwidth" is the number of packets per "step" along the cable. This would be most analagous to the higher frequency of CAT cables that higher-rated cables (and ports) use to achieve higher bandwidth.
* Packets are the fundamental unit
  * Unlike the real world, packets are transmitted as a single discrete unit, irrelevant of size.
  * Packets are also structured Python objects, for ease of inspection and exploration/understanding of protocols, rather than being raw binary data. The idea is to teach "IP Packets are encapsulated in an Ethernet packet have a source and destination IP address" rather than "these x bytes of the IP data frame portion of the packet contains y data".
* Device packet processing
  * By default, devices are configured to be able to read the combined bandwidth of all ports every step. This will, by default, ensure the inbound buffers can never fill. This can be tweaked to slow the processing of packets to allow for "overwhelming" a host and dropping packets.
    * On switches, this default can easily lead to overflowing of outbound buffers on popular destination ports, unless those are manually increased.
    * For simplicity, "applications" listening on a host, can process and respond to a packet (or multiple packets) within the same step, without any kind of time delay for processing like the real world would normally see.

## TODO
Known missing things that might get implemented

* ICMP Error messages - Currently missing, both generating/sending and processing received errors
* TCP - Requires a bit more tracking, still making sure the basics are all worked out
* VLANs - May require some rework of some parts to support, but likely worth implementing as the concepts are pretty useful
* (R)STP - Might be out of scope. Lets be honest, though, if you know what this is, this really isn't for you anyway. 😉
* Port bonding and LACP - might be fun, might also be out of scope (at least short-term)

## Basic Usage

Note: This section is intended to be used as a quick "how to use the simulator", and will be light on explaining networking concepts.

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

By default, `Device`s have a single port, and `Switch`es have 4. You can see the current state of the simulation, and see that the devices have been added with the `show()` function, which will output all devices and their ports (including their hardware ("MAC") addresses), as well as their in/out queue sizes.

```
sim.show()
```

They aren't connected yet, however, we need to connect them, which we can do two ways:

Manually creating a cable, connecting it to the device ports, and adding it to the simulation:
```
from networksim.hardware.cable import Cable

cable_A_SW = Cable(A[0], SW[0])
sim.add_cable(cable_A_SW)
```

Having the simulation create the cable and connect to the first available (unused) port on a device for you (which will, additionally, add the devices to the simulation if they aren't already):
```
sim.connect_devices(B, SW)
```

After that, both devices should be connected to the switch. Both methods, by default, will create cables of length 3 with a bandwidth of 1. You can check the new state with `sim.show()` and see the cables connecting the devices to the switch, as well as see any packets traveling along the cables (which should be none).

Now that we have both devices connected to the switch, they should be able to send Ethernet packets to each other. We can send a packet from A to B with the following:

```
A[0].send(EthernetPacket(dst=B[0].hwid, payload="Hello B!"))
```

And a `sim.show()` will show that Port[0] on device A has a packet on the outbound queue. If we advance the simulation by 1 (`sim.step()`), we can see the packet on the cable between A and the switch by running `show()` again.

If we advance the simulation 3 more times (`sim.step(3)`), we can see a packet on the outbound queue of Port[1] of SW. As well as an entry for A's hardware address in the switch's CAM table (more on that later).

Advancing the simulation 4 more steps will show a packet on the inbound queue for B. Unlike `Switch`es (and, later, `IPDevice`s), basic Ethernet `Device`s don't automatically process packets from their queue by default. But we can manually read the packet from the port ourselves.

```
B[0].receive().payload
```

The list of all devices in the simulation can be accessed with:

```
sim.devices
```

## Additional devices
In addition to `Device`s and `Switch`es, there are also:

* `IPDevice`
  * Basic network device with an IP stack, supports IP networking.
  * Import:
    * ```
      from networksim.hardware.device.ip.ipdevice import IPDevice
      ```
* `Router`
  * Comes with an IP stack and can move packets between IP networks
  * Imports (both are equivelant):
    * ```
      from networksim.hardware.device.ip.router import Router
      ```
    * ```
      from networksim.hardware.device.infrastructure.router import Router
      ```

## Tutorials/Lessons
(These are still a WIP)
* [Ethernet Basics](./docs/Ethernet_Basics.md)
* [IP Basics](./docs/IP_Basics.md)
* [Routing Basics](./docs/Routing_Basics.md)

## Example networks
### Tier-3 Network
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

To use and play with this network:

```
from networksim.examples.tier3_network import sim
```

### Routing
Creates two networks connected with a router. Each network has a switch, a DHCP server, and 2 clients.

```
         Router
        /      \
     SW1        SW2
    / | \      / | \
DHCP  A1 A2  B1 B2  DHCP
```

To use and play with this network:

```
from networksim.examples.simple_routing import sim
```
