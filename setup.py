from setuptools import setup, find_packages

setup(

    name='statuspage',
    version='0.1-dev',
    description='Internal status page',
    url='http://github.com/westernx/statuspage',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    
    author='Mike Boers',
    author_email='statuspage@mikeboers.com',
    license='BSD-3',
    
    install_requires=[
        'psutil',
    ],

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    
)
