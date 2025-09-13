from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="car_rental",
    version="0.0.1",
    description="Car Rental Management App for Frappe/ERPNext",
    author="Your Name",
    author_email="you@example.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)