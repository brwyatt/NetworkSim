from networksim.application.dhcp.client import DHCPClient
from networksim.application.dhcp.server import DHCPServer
from networksim.application.ping import Ping
from networksim.hardware.device.infrastructure.switch import Switch
from networksim.hardware.device.ip.ipdevice import IPDevice
from networksim.hardware.device.ip.router import Router
from networksim.ipaddr import IPAddr
from networksim.ipaddr import IPNetwork
from networksim.simulation import Simulation


sim = Simulation()

dhcp_serverA_ip = IPAddr.from_str("172.16.1.5")
dhcp_networkA = IPNetwork(dhcp_serverA_ip, 24)
router_ipA = IPAddr(
    int.to_bytes(
        int.from_bytes(dhcp_networkA.addr.byte_value, "big") + 1,
        IPAddr.length_bytes,
        "big",
    ),
)

dhcp_serverB_ip = IPAddr.from_str("172.20.5.5")
dhcp_networkB = IPNetwork(dhcp_serverB_ip, 24)
router_ipB = IPAddr(
    int.to_bytes(
        int.from_bytes(dhcp_networkB.addr.byte_value, "big") + 1,
        IPAddr.length_bytes,
        "big",
    ),
)

SW1 = Switch(name="SW1")
SW2 = Switch(name="SW2")

router = Router(name="router")
sim.connect_devices(router, SW1)
sim.connect_devices(router, SW2)
router.ip.bind(router_ipA, dhcp_networkA, router[0])
router.ip.bind(router_ipB, dhcp_networkB, router[1])

dhcp_serverA = IPDevice(name="dhcp_server_a")
sim.connect_devices(dhcp_serverA, SW1)
dhcp_serverA.ip.bind(dhcp_serverA_ip, dhcp_networkA, dhcp_serverA[0])
dhcp_serverA.add_application(DHCPServer, "dhcp_server")
dhcp_serverA.start_application(
    "dhcp_server",
    network=dhcp_networkA,
    router=router_ipA,
)

dhcp_serverB = IPDevice(name="dhcp_server_b")
sim.connect_devices(dhcp_serverB, SW2)
dhcp_serverB.ip.bind(dhcp_serverB_ip, dhcp_networkB, dhcp_serverB[0])
dhcp_serverB.add_application(DHCPServer, "dhcp_server")
dhcp_serverB.start_application(
    "dhcp_server",
    network=dhcp_networkB,
    router=router_ipB,
)

A1 = IPDevice(name="a1")
sim.connect_devices(A1, SW1)
A1.add_application(Ping, "ping")
A1.add_application(DHCPClient, "dhcp_client")
A1.start_application("dhcp_client")

A2 = IPDevice(name="a2")
sim.connect_devices(A2, SW1)
A2.add_application(Ping, "ping")
A2.add_application(DHCPClient, "dhcp_client")
A2.start_application("dhcp_client")

B1 = IPDevice(name="b1")
sim.connect_devices(B1, SW2)
B1.add_application(Ping, "ping")
B1.add_application(DHCPClient, "dhcp_client")
B1.start_application("dhcp_client")

B2 = IPDevice(name="b2")
sim.connect_devices(B2, SW2)
B2.add_application(Ping, "ping")
B2.add_application(DHCPClient, "dhcp_client")
B2.start_application("dhcp_client")
