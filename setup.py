from setuptools import setup

setup(
    name='snitch',
    packages=['snitch'],
    version='0.2',
    author='Ronald Evers',
    author_email='ronald@ch10.nl',
    url='https://github.com/ronaldevers/snitch',
    description='JSON log formatter and Sentry client',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Logging'],
    install_requires=['raven', 'requests'],
    entry_points={'console_scripts': ['snitch = snitch.snitch.main']},
)
