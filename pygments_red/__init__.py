# -*- coding: utf-8 -*-
"""
    Red lexer
    ~~~~~~~~~~~

    Pygments lexer for Ruby + Red.

    :copyright: Copyright 2012 Hugo Maia Vieira
    :license: BSD, see LICENSE for details.
"""

from pygments.lexers.agile import RubyLexer
from pygments.token import Name, Keyword

class RedLexer(RubyLexer):
    name = 'Red'
    aliases = ['red']
    filenames = ['*.red'] # just to have one if you whant to use

    EXTRA_KEYWORDS = ['abstract_record', 'abstract_machine', 'record', 'machine', 'event', 'set', 'seq', 'requires', 'ensures', 'from', 'to', 'params', 'policy', 'principal', 'restrict', 'reject', 'refs', 'owns', 'fields']

    def get_tokens_unprocessed(self, text):
        for index, token, value in RubyLexer.get_tokens_unprocessed(self, text):
            if token is Name and value in self.EXTRA_KEYWORDS:
                yield index, Keyword, value
            else:
                yield index, token, value
