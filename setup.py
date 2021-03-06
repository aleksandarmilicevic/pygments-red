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
                    ruby193=pygments_red:Ruby193Lexer
                    arby=pygments_red:ARbyLexer
                    red=pygments_red:RedLexer
                    sunny=pygments_red:SunnyLexer
                    handlebars=pygments_red:HandlebarsLexer
                    html+handlebars=pygments_red:HandlebarsHtmlLexer
                    slang=pygments_red:SlangLexer
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
