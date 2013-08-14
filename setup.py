#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='pygments-red',
    version='0.2',
    description='Pygments lexer for Ruby + Red.',
    keywords='pygments ruby red lexer',
    license='MIT',

    author='Aleksandar Milicevic',
    author_email='aleks@csail.mit.edu',

    url='https://github.com/aleksandarmilicevic/pygments-red',

    packages=find_packages(),
    install_requires=['pygments >= 1.4'],

    entry_points='''[pygments.lexers]
                    redruby=pygments_red:RedRubyLexer
                    red=pygments_red:RedLexer
                    errb=pygments_red:ErrbLexer
                    ered=pygments_red:EredLexer
                    redhtml=pygments_red:RedHtmlLexer

                    [pygments.styles]
                    redstyle=pygments_red:RedStyle
                    github=pygments_red:GithubStyle
                    githubcustom=pygments_red:GithubCustom1Style''',

    classifiers=[
    ],
)
