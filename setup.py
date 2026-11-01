from setuptools import setup, find_packages

setup(
    name="richardlab",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1,<4",
        "psutil",
        "requests",
    ],
)
