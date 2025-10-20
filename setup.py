from setuptools import setup, find_packages

setup(
    name="zit",
    version="0.6.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "zit=zit.cli:cli",
            "zit-fm=zit.fm.filemanager_cli:fm",
            "zit-git=zit.git.git_cli:git_cli",
            "zit-sys=zit.sys.sys_cli:sys_cli",
        ],
    },
)
