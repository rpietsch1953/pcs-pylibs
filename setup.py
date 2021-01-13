import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pcs_argpass",
    version="0.3.1",
    author="Rainer Pietsch",
    author_email="r.pietsch@pcs-at.com",
    description="Argument parser and checker",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rpietsch1953/pcs-pylibs",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
	"License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
    ],
)

