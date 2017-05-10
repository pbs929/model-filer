from setuptools import setup, find_packages

setup(
    name='ds_model_filer',
    version='0.1.0',

    packages=find_packages(),

    install_requires=[
        "dill",
        "boto3"
        ],
    )
