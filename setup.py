import setuptools

with open("requirements.txt") as f:
	requires = f.readlines()

setuptools.setup(
	name="inquisitor",
	version="0.0.1",
	author="Tim Van Baak",
	description="An arbitrary feed aggregator",
	packages=setuptools.find_packages(),
	python_requires=">=3.6",
	install_requires=requires,
)
