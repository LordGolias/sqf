from setuptools import setup

setup(
    name='sqflint',
    version='0.1.0',
    author='Lord Golias',
    author_email='lord.golias1@gmail.com',
    description='A SQF (Arma) linter',
    url='https://github.com/LordGolias/sqf',
    license='BSD',
    py_modules=['sqf'],
    include_package_data=True,
    scripts=[
        'sqflint.py'
    ],
    entry_points={
        'console_scripts': [
            'sqflint = sqflint:_main',
        ],
    },
    classifiers=[
        'Environment :: Console',
    ],
)
