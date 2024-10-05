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
    },
    install_requires=[],
    tests_require=[],
)
