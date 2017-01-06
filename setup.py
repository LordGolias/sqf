from setuptools import setup, find_packages, Extension


setup(name='tokenizer',
      version='1.0',
      packages=find_packages(),
      license='MIT',
      #ext_package='tokenizer',
      ext_modules=[Extension("_tokenizer",
                             ["sqf/tokenizer_source/tokenizer.cpp"])]
)
