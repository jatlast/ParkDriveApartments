from setuptools import setup, find_packages

# Step 5: Manage Versions
#   When you update pkdr_utils, increase the version in setup.py (e.g., 0.1.1), rebuild the package, and reinstall it.
#   This will allow other projects to use the new version of pkdr_utils.
#   If you make a breaking change, increase the major version number (e.g., 1.0.0).
#   If you make a backwards-compatible change, increase the minor version number (e.g., 0.2.0).
#   If you make a backwards-compatible bug fix, increase the patch version number (e.g., 0.1.1).
setup(
    name="pkdr_utils",
    version="0.2.1",
    description="Custom utilities for Park Drive Apartments projects",
    author="Jason Baumbach",
    author_email="jatlast@hotmail.com",
    packages=find_packages(),  # Automatically find all packages (like pkdr_utils)
    install_requires=[
        "PyYAML>=6.0.2",  # Ensure pyyaml is installed
        "mysql-connector-python>=8.0.0",  # Ensure MySQL connector is installed
        # "mysql_connector_repackaged>=0.3.1",  # Ensure MySQL connector is installed
    ],
    classifiers=[
        "Programming Language :: Python :: 3", 
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

# Step 6: Build the Package
#   Run the following command to build the package:
#     On the Windows Dev Box...
#	    python Z:\PkDr\HA\code\DEV\python\setup.py sdist bdist_wheel
#     within the activated virtual environment...
#	    python /home/PkDr/HA/code/DEV/python/setup.py sdist bdist_wheel

# Step 8: Install the Package
#   Run the following command to install the package:
#     within the Windows Dev Box...
#	    pip install Z:\PkDr\HA\code\DEV\python\dist\pkdr_utils-0.2.1-py3-none-any.whl
#     within the activated virtual environment...
#	    pip install /home/PkDr/HA/code/DEV/python/dist/pkdr_utils-0.2.1-py3-none-any.whl
