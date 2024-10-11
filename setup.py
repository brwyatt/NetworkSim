from setuptools import find_packages
from setuptools import setup


setup(
    name="networksim",
    version="0.1.0",
    author="Bryan Wyatt",
    author_email="brwyatt@gmail.com",
    description=(""),
    license="GPLv3",
    keywords="network networking simulator education educational",
    url="https://github.com/brwyatt/NetworkSim",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={"networksim": []},
    python_requires="~=3.6",
    include_package_data=False,
    entry_points={
        "console_scripts": ["networksim = networksim.ui:start_ui"],
        "networksim_device_types": [
            "Device = networksim.hardware.device:Device",
            "IPDevices.IPDevice = networksim.hardware.device.ip.ipdevice:IPDevice",
            "IPDevices.Router = networksim.hardware.device.ip.router:Router",
            "Infrastructrue.Router = networksim.hardware.device.infrastructure.router:Router",
            "Infrastructrue.Switch = networksim.hardware.device.infrastructure.switch:Switch",
        ],
        "networksim_applications": [
            "Ping = networksim.application.ping:Ping",
            "DHCP_Server = networksim.application.dhcp.server:DHCPServer",
            "DHCP_Client = networksim.application.dhcp.client:DHCPClient",
        ],
    },
    install_requires=["setuptools>=50.0.0,<76.0.0"],
    tests_require=[],
)
