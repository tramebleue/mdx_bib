from setuptools import setup

setup(name='mdx_bib',
      description="A Python markdown extension for handling citations.",
      version='0.0.1',
      author = 'Darwin Darakananda',
      packages=['mdx_bib'],
      install_requires = ['markdown', 'pybtex'],
      license='MIT')
