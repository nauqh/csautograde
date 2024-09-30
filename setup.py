from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    description = f.read()

setup(
    name='csautograde',
    version='0.2.0',
    description='An internal tool for exam autograding',
    author='Obiwan',
    author_email='quan.do@coderschool.vn',
    packages=find_packages(),
    install_requires=[

    ],
    long_description=description,
    long_description_content_type='text/markdown',
)
