"""天眼 (Tianyan) setup."""

from setuptools import setup, find_packages

setup(
    name="tianyan",
    version="0.1.0",
    description="天眼 — 基于多Agent人群模拟的中国商业预测平台",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="MoKangMedical",
    url="https://github.com/MoKangMedical/tianyan",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.0.0",
        "httpx>=0.27.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
    ],
)
