from typing import Any
from typing import Dict
from typing import Optional

from networksim.hwid import HWID
from networksim.ipaddr import IPAddr
from networksim.packet.payload import Payload


class DHCPPayload(Payload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_hwid: Optional[HWID] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        self.client_ip = client_ip
        self.your_ip = your_ip
        self.server_ip = server_ip
        self.gateway_ip = gateway_ip
        self.client_hwid = client_hwid

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
        client_hwid: Optional[HWID] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_hwid,
            options,
        )


class DHCPOffer(DHCPPayload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_hwid: Optional[HWID] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_hwid,
            options,
        )


class DHCPRequest(DHCPPayload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_hwid: Optional[HWID] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_hwid,
            options,
        )


class DHCPAck(DHCPPayload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_hwid: Optional[HWID] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_hwid,
            options,
        )


class DHCPNack(DHCPPayload):
    def __init__(
        self,
        client_ip: Optional[IPAddr] = None,
        your_ip: Optional[IPAddr] = None,
        server_ip: Optional[IPAddr] = None,
        gateway_ip: Optional[IPAddr] = None,
        client_hwid: Optional[HWID] = None,
        options: Optional[Dict[int, Any]] = None,
    ):
        super().__init__(
            client_ip,
            your_ip,
            server_ip,
            gateway_ip,
            client_hwid,
            options,
        )
