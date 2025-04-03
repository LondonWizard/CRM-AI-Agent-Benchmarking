from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("crm_benchmark_lib/requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="crm-benchmark-lib",
    version="0.1.0",
    author="CRM AI Agent Challenge Team",
    author_email="aiagentchallenge@gmail.com",
    description="A library for benchmarking CRM AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/CRM-AI-Agent-Benchmarking",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.7",
    package_data={
        "crm_benchmark_lib": [
            "dataset_questions/*.json",
            "generated_csvs/*.csv",
        ],
    },
) 