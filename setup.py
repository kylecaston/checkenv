import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="checkenv",
    version="1.0.0",
    author="Kyle Caston",
    author_email="kyle@caston.dev",
    description="Ensures specified environment variables are present during runtime",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kylecaston/checkenv",
    packages=setuptools.find_packages(),
    install_requires=[
        'jsonschema',
        'colorama',
        'future'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',
)
