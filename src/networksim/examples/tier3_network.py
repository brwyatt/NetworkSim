from random import choice
from random import randint

from networksim.application.dhcp.client import DHCPClient
from networksim.application.dhcp.server import DHCPServer
from networksim.application.ping import Ping
from networksim.hardware.cable import Cable
from networksim.hardware.device.infrastructure.switch import Switch
from networksim.hardware.device.ip.ipdevice import IPDevice
from networksim.ipaddr import IPAddr
from networksim.ipaddr import IPNetwork
from networksim.simulation import Simulation


sim = Simulation()

# CORE Switch
cor_sw = Switch(name="cor_sw", iface_count=4, forward_capacity=1600)
for iface in cor_sw.ifaces:
    iface.max_bandwidth = 400
sim.add_device(cor_sw)


# Aggregation Switches
def create_agg(name):
    sw = Switch(name=name, iface_count=10, forward_capacity=1500)
    for iface in sw.ifaces[:-2]:
        iface.max_bandwidth = 100
    for iface in sw.ifaces[-2:]:
        iface.max_bandwidth = 400
    return sw


agg_sw1 = create_agg(name="agg_sw1")
sim.add_device(agg_sw1)
sim.add_cable(Cable(agg_sw1[-1], cor_sw[0], length=1, max_bandwidth=400))

agg_sw2 = create_agg(name="agg_sw2")
sim.add_device(agg_sw2)
sim.add_cable(Cable(agg_sw2[-1], cor_sw[1], length=5, max_bandwidth=400))


# Access Switches
def create_acc(name):
    sw = Switch(name=name, iface_count=26, forward_capacity=400)
    for iface in sw.ifaces[:-2]:
        iface.max_bandwidth = 10
    for iface in sw.ifaces[-2:]:
        iface.max_bandwidth = 100
    return sw


acc_sw1_1 = create_acc(name="acc_sw1_1")
sim.add_device(acc_sw1_1)
sim.add_cable(Cable(acc_sw1_1[-1], agg_sw1[0], length=1, max_bandwidth=100))

acc_sw1_2 = create_acc(name="acc_sw1_2")
sim.add_device(acc_sw1_2)
sim.add_cable(Cable(acc_sw1_2[-1], agg_sw1[1], length=1, max_bandwidth=100))

acc_sw2_1 = create_acc(name="acc_sw2_1")
sim.add_device(acc_sw2_1)
sim.add_cable(Cable(acc_sw2_1[-1], agg_sw2[0], length=1, max_bandwidth=100))

acc_sw2_2 = create_acc(name="acc_sw2_2")
sim.add_device(acc_sw2_2)
sim.add_cable(Cable(acc_sw2_2[-1], agg_sw2[1], length=1, max_bandwidth=100))

# DHCP Server
dhcp_server_ip = IPAddr.from_str("172.16.20.5")
dhcp_network = IPNetwork(dhcp_server_ip, 24)

dhcp_server = IPDevice(name="dhcp_server")
dhcp_server.ifaces[0].max_bandwidth = 20
sim.add_device(dhcp_server)
sim.add_cable(
    Cable(
        dhcp_server[0],
        choice(
            [
                x
                for x in (agg_sw1.ifaces[:-2] + agg_sw2.ifaces[:-2])
                if not x.connected
            ],
        ),  # add to AGG switch for bandwidth reasons
        length=1,
        max_bandwidth=20,
    ),
)
dhcp_server.ip.bind(dhcp_server_ip, dhcp_network, dhcp_server[0])
dhcp_server.add_application(DHCPServer, "dhcp_server")
dhcp_server.start_application(
    "dhcp_server",
    network=dhcp_network,
)


# Client devices
def add_device():
    available_ifaces = [
        x
        for x in (
            acc_sw1_1.ifaces[:-2]
            + acc_sw1_2.ifaces[:-2]
            + acc_sw2_1.ifaces[:-2]
            + acc_sw2_2.ifaces[:-2]
        )
        if not x.connected
    ]
    dev = IPDevice()
    dev.ifaces[0].max_bandwidth = 10
    sim.add_device(dev)
    sim.add_cable(
        Cable(
            dev[0],
            choice(available_ifaces),
            length=randint(1, 6),
            max_bandwidth=10,
        ),
    )
    dev.add_application(Ping, "ping")
    dev.add_application(DHCPClient, "dhcp_client")
    dev.start_application("dhcp_client")


def add_devices(count):
    for _ in range(0, count):
        add_device()
        sim.step(randint(1, 30))


add_devices(50)
