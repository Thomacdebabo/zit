from setuptools import setup, find_packages

setup(
    name="zit",
    version="0.2.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'zit=zit.cli:cli',
            'zit-fm=zit.filemanager_cli:fm',
        ],
    },
) 