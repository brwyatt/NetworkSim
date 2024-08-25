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
        "console_scripts": ["networksim = networksim.cli:main"],
    },
    install_requires=[],
    tests_require=[],
)
