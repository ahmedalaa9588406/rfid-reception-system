"""Setup script for RFID Reception System."""

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='rfid-reception-system',
    version='1.0.0',
    description='Python-based offline reception system for RFID amusement park card system',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Ahmed Alaa',
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'rfid-reception=rfid_reception.app:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
    ],
)
