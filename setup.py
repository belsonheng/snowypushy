from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

# python setup.py sdist bdist_wheel
setup(
    name='snowypushy',
    packages=find_packages(),
    version='0.3.8',
    description='Snowy helps us download and upload data across various data sources (e.g. Snowflake, Oracle, SAP Hana and Domo).',
    long_description=readme(),
    long_description_content_type='text/markdown',
    author='Belson Heng',
    author_email='belsonheng@hotmail.com',
    url='https://github.com/belsonheng/snowypushy',
    download_url='https://github.com/belsonheng/snowypushy/archive/v0.3.8.tar.gz',
    keywords=['data', 'migration', 'snowflake', 'domo'],
    license='MIT',
    install_requires=[
        'hvac==0.9.6',
        'cryptography==2.8',
        'snowflake-sqlalchemy==1.2.0',
        'SQLAlchemy==1.3.7',
        'pandas==0.25.1',
        'numpy==1.16.4',
        'PyYAML==5.1.2',
        'pydomo==0.2.3',
        'tqdm==4.36.1',
        'idna==2.8'
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3'],
    include_package_data=True,
    zip_safe=False
)
