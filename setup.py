from setuptools import setup

setup(
    name='WebIt',
    version='0.1',
    author='Ian Johnson',
    author_email='tacoda@pm.me',
    description='WebIt is a tool to deploy static websites to AWS',
    license='GPLv3+',
    packages=['webit'],
    url='www.tacoda.me/webit.html',
    install_requires=[
        'boto3',
        'click'
    ],
    entry_points='''
        [console_scripts]
        webit=webit.webit:cli
    '''
)
