# -*- coding: utf-8 -*-
"""
    Red lexer
    ~~~~~~~~~~~

    Pygments lexer for Ruby + Red.

    :copyright: Copyright 2012 Hugo Maia Vieira
    :license: BSD, see LICENSE for details.
"""

from pygments.lexer import bygroups
from pygments.lexers.agile import RubyLexer
from pygments.token import Token, Keyword, Name, Comment, String, Error, Number, Operator, Generic, Literal

import sys
import collections

class RedLexer(RubyLexer):
    name = 'Red'
    aliases = ['red']
    filenames = ['*.red'] # just to have one if you whant to use

    CLASS_GEN_KEYWORDS = ['abstract_record', 'abstract_machine', 'record', 'machine', 'event', 'policy']
    EXTRA_KEYWORDS = CLASS_GEN_KEYWORDS + ['set', 'seq', 'requires', 'ensures', 'from', 'to', 'params', 'principal', 'restrict', 'reject', 'refs', 'owns', 'fields']

    tokens = {}
    tokens.update(RubyLexer.tokens)

    # change rule 
    #
    #   (r'([a-zA-Z_][a-zA-Z0-9]*)(:)', bygroups(String.Symbol, Token.Punctuation)
    # to 
    #   (r'([a-zA-Z_][a-zA-Z0-9]*)(:)(?!:)', bygroups(String.Symbol, Token.Punctuation)
    #
    # so that fully qualified names (e.g., X::Y::Z) are lexed properly, meaning
    #
    #   ('X', Constant), ('::', Operator), ('Y', Constant)
    # instead of
    #   ('X', Symbol), (':', Punctuation), (':Y', Symbol)
    string_rules = tokens['strings']
    string_rules[4] = (r'([a-zA-Z_][a-zA-Z0-9]*)(:)(?!:)', bygroups(String.Symbol, Token.Punctuation))
    
    def get_tokens_unprocessed(self, text):        
        lookahead = 1
        lookbehind = 1
        queue = collections.deque()
        processed = collections.deque([], lookbehind)
        def next(): 
            if len(queue) > 0: 
                return queue[0]
            else: 
                return (None, None, None)
        def prev(): 
            if len(processed) > 0: 
                return processed[-1]
            else: 
                return (None, None, None)
        def _idx(t): return (t[0] if t is not None else None)
        def _token(t): return (t[1] if t is not None else None)
        def _value(t): return (t[2] if t is not None else None)

        def process_one():
            def process(res):
                # print >> sys.stderr, "%s '%s'" % (res[1], res[2])
                if _token(res) is not Token.Text: 
                    processed.append(res)
                return res

            curr = queue.popleft()
            curr_idx, curr_token, curr_value = curr

            # convert Name tokens to Keyword for extra Red keywords
            if curr_token is Name and curr_value in self.EXTRA_KEYWORDS:
                return process((curr_idx, Keyword, curr_value))

            # convert Name.Constant tokens to Name.Class for names following Red class generating keywords
            if curr_token is Name.Constant and _token(prev()) is Keyword and _value(prev()) in self.CLASS_GEN_KEYWORDS:
                return process((curr_idx, Name.Class, curr_value))
            
            # remove weird lexing rule that says that "name" is a buildin keyword
            if curr_value == "name" and curr_token is Name.Builtin and _token(next()) is Token.Punctuation:
                return process((curr_idx, Literal.String.Symbol, curr_value))

            return process(curr)
             
        for index, token, value in RubyLexer.get_tokens_unprocessed(self, text):
            queue.append((index, token, value))
            if len(queue) < 1 + lookahead: continue
            ans = process_one()
            if ans is not None: yield ans
                    
        while (len(queue) > 0):
            ans = process_one()
            if ans is not None: yield ans

from pygments.style import Style
from pygments.styles import get_style_by_name


class RedStyle(Style):
    default_style = ""

    styles = {}

    base = get_style_by_name("tango")
    for token in base.styles.keys():
        styles[token] = base.styles[token]

    const_style = '#000000'
    styles[Name.Constant] = const_style
    styles[Name.Class] = 'bold ' + const_style    
    styles[Name.Namespace] = const_style
