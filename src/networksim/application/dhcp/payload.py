from typing import Any
from typing import Dict
from typing import Optional

from networksim.addr.ipaddr import IPAddr
from networksim.addr.macaddr import MACAddr
from networksim.packet.payload import Payload


class DHCPPayload(Payload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_macaddr: Optional[MACAddr] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        self.client_ip = client_ip
        self.your_ip = your_ip
        self.server_ip = server_ip
        self.gateway_ip = gateway_ip
        self.client_macaddr = client_macaddr

        if options is None:
            options = {}
        self.options = options


class DHCPDiscover(DHCPPayload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_macaddr: Optional[MACAddr] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_macaddr,
            options,
        )


class DHCPOffer(DHCPPayload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_macaddr: Optional[MACAddr] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_macaddr,
            options,
        )


class DHCPRequest(DHCPPayload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_macaddr: Optional[MACAddr] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_macaddr,
            options,
        )


class DHCPAck(DHCPPayload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_macaddr: Optional[MACAddr] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_macaddr,
            options,
        )


class DHCPNack(DHCPPayload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_macaddr: Optional[MACAddr] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_macaddr,
            options,
        )
