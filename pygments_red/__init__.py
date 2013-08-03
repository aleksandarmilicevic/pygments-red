# -*- coding: utf-8 -*-
"""
    Red lexer
    ~~~~~~~~~~~

    * some fixes to RubyLexer --- class RedRubyLexer
    * lexer for Ruby + Red --- class RedLexer
    * some styles
"""
from pygments.lexers.web import HtmlLexer
from pygments.lexer import bygroups, DelegatingLexer
from pygments.lexers.agile import RubyLexer, RegexLexer
from pygments.lexers.templates import ErbLexer
from pygments.token import Token, Text, Keyword, Name, Comment, String, Error, Number, Operator, Generic, Literal

import sys
import collections


def _idx(t):   return (t[0] if t is not None else None)
def _token(t): return (t[1] if t is not None else None)
def _value(t): return (t[2] if t is not None else None)

"""
--------------------------------------------------------------------------------
  Common lexer class that implements lookahed and lookbehind buffers.
--------------------------------------------------------------------------------
"""
class RedLexerBase(RegexLexer):

    lookahead = 1
    lookbehind = 1
    queue = collections.deque()
    processed = collections.deque([], lookbehind)

    def next(self):
            if len(self.queue) > 0:
                return self.queue[0]
            else:
                return (None, None, None)
    def prev(self):
        if len(self.processed) > 0:
            return self.processed[-1]
        else:
            return (None, None, None)

    def process_one(self, curr):
        raise Exception('must override')

    def get_tokens_unprocessed(self, text):
        def __process(res):
            # print >> sys.stderr, "%s '%s'" % (res[1], res[2])
            if res is not None and _token(res) is not Token.Text:
                self.processed.append(res)
            return res

        for index, token, value in RegexLexer.get_tokens_unprocessed(self, text):
            self.queue.append((index, token, value))
            if len(self.queue) < 1 + self.lookahead: continue
            curr = self.queue.popleft()
            ans = __process(self.process_one(curr))
            if ans is not None:
                yield ans

        while (len(self.queue) > 0):
            ans = __process(self.process_one(self.queue.popleft()))
            if ans is not None: yield ans

"""
--------------------------------------------------------------------------------
(1) Change rule

      (r'([a-zA-Z_][a-zA-Z0-9]*)(:)', bygroups(String.Symbol, Token.Punctuation)
    to
      (r'([a-zA-Z_][a-zA-Z0-9]*)(:)(?!:)', bygroups(String.Symbol, Token.Punctuation)

    so that fully qualified names (e.g., X::Y::Z) are lexed properly, meaning

      ('X', Constant), ('::', Operator), ('Y', Constant)
    instead of
      ('X', Symbol), (':', Punctuation), (':Y', Symbol)

(2) Remove "name" from builtin keywords
--------------------------------------------------------------------------------
"""
class RedRubyLexer(RedLexerBase):
    name = 'RedRuby'
    aliases = ['redruby']
    filenames = ['*.rb'] # just to have one if you whant to use

    tokens = {}
    tokens.update(RubyLexer.tokens)

    string_rules = tokens['strings']
    string_rules[4] = (r'([a-zA-Z_][a-zA-Z0-9]*)(:)(?!:)', bygroups(String.Symbol, Token.Punctuation))

    def process_one(self, curr):
        curr_idx, curr_token, curr_value = curr

        # remove weird lexing rule that says that "name" is a buildin keyword
        if curr_value == "name" and curr_token is Name.Builtin and _token(self.next()) is Token.Punctuation:
            return (curr_idx, Literal.String.Symbol, curr_value)

        return curr

"""
--------------------------------------------------------------------------------
(1) Adds new keywords

(2) Converts tokens following class generating keywords in Red from
    Name.Constant to Name.Class

(3) Emphasize certain Red builtin functions (e.g., 'render')
--------------------------------------------------------------------------------
"""
class RedLexer(RedRubyLexer):
    name = 'Red'
    aliases = ['red']
    filenames = ['*.red'] # just to have one if you whant to use

    CLASS_GEN_KEYWORDS = ['abstract_record', 'abstract_machine', 'record', 'machine', 'event', 'policy']
    OTHER_KEYWORDS = ['set', 'seq', 'requires', 'ensures', 'from', 'to', 'params', 'principal', 'restrict', 'reject', 'refs', 'owns', 'fields']
    EXTRA_KEYWORDS = CLASS_GEN_KEYWORDS + OTHER_KEYWORDS

    EMPH_FUNCS = ['render']

    tokens = {}
    tokens.update(RedRubyLexer.tokens)

    def process_one(self, curr):
        curr_idx, curr_token, curr_value = curr

        # convert Name tokens to Name.Builtin.Pseudo for emphasized Red functions
        if curr_token is Name and curr_value in self.EMPH_FUNCS:
            return (curr_idx, Name.Builtin.Pseudo, curr_value)

        # convert Name tokens to Keyword for extra Red keywobrds
        if curr_token is Name and curr_value in self.EXTRA_KEYWORDS:
            return (curr_idx, Keyword, curr_value)

        # convert Name.Constant tokens to Name.Class for names following Red class generating keywords
        if curr_token is Name.Constant and _token(self.prev()) is Keyword and _value(self.prev()) in self.CLASS_GEN_KEYWORDS:
            return (curr_idx, Name.Class, curr_value)

        return RedRubyLexer.process_one(self, curr)



"""
--------------------------------------------------------------------------------
Like ERB except that it uses RedRubyLexer for ruby expressions
--------------------------------------------------------------------------------
"""
class ErrbLexer(ErbLexer):
    name = 'ERRB'
    aliases = ['erb', 'errb']
    mimetypes = ['application/x-ruby-templating']
    def __init__(self, **options):
        ErbLexer.__init__(self, **options)
        self.ruby_lexer = RedRubyLexer(**options)

"""
--------------------------------------------------------------------------------
Like ERB except that it uses RedLexer for ruby expressions
--------------------------------------------------------------------------------
"""
class EredLexer(ErbLexer):
    name = 'ERed'
    aliases = ['erb', 'ered']
    mimetypes = ['application/x-ruby-templating']
    def __init__(self, **options):
        ErbLexer.__init__(self, **options)
        self.ruby_lexer = RedLexer(**options)

"""
--------------------------------------------------------------------------------
Like RhtmlLexer except that it uses EredLexer for ruby expressions
--------------------------------------------------------------------------------
"""
class RedHtmlLexer(DelegatingLexer):
    name = 'RedHTML'
    aliases = ['redhtml', 'html+ered', 'html+red']
    filenames = ['*.redhtml']
    mimetypes = ['text/html+red']

    def __init__(self, **options):
        super(RedHtmlLexer, self).__init__(HtmlLexer, EredLexer, **options)

    def analyse_text(text):
        rv = EredLexer.analyse_text(text) - 0.01
        if html_doctype_matches(text):
            # one more than the XmlErbLexer returns
            rv += 0.5
        return rv

############################################################################


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


class GithubStyle(Style):
    default_style = ""
    styles = {
        Comment:                      '#999988 italic',
        Error:                        '#a61717 bg:#e3d2d2',
        Keyword:                      '#000000 bold',
        Operator:                     '#000000 bold',
        Comment.Multiline:            '#999988 italic',
        Comment.Preproc:              '#999999 bold italic',
        Comment.Single:               '#999988 italic',
        Comment.Special:              '#999999 bold italic',
        Generic.Deleted:              '#000000 bg:#ffdddd',
        Generic.Emph:                 '#000000 italic',
        Generic.Error:                '#aa0000',
        Generic.Heading:              '#999999',
        Generic.Inserted:             '#000000 bg:#ddffdd',
        Generic.Output:               '#888888',
        Generic.Prompt:               '#555555',
        Generic.Strong:               'bold',
        Generic.Subheading:           '#aaaaaa',
        Generic.Traceback:            '#aa0000',
        Keyword.Constant:             '#000000 bold',
        Keyword.Declaration:          '#000000 bold',
        Keyword.Namespace:            '#000000 bold',
        Keyword.Pseudo:               '#000000 bold',
        Keyword.Reserved:             '#000000 bold',
        Keyword.Type:                 '#445588 bold',
        Literal.Number:               '#009999',
        Literal.String:               '#d01040',
        Name.Attribute:               '#008080',
        Name.Builtin:                 '#0086B3',
        Name.Class:                   '#445588 bold',
        Name.Constant:                '#008080', #'#445588', # '#004380', #
        Name.Decorator:               '#3c5d5d bold',
        Name.Entity:                  '#800080',
        Name.Exception:               '#990000 bold',
        Name.Function:                '#990000 bold',
        Name.Label:                   '#990000 bold',
        Name.Namespace:               '#555555',
        Name.Tag:                     '#000080',
        Name.Variable:                '#008080',
        Operator.Word:                '#000000 bold',
        Text.Whitespace:              '#bbbbbb',
        Literal.Number.Float:         '#009999',
        Literal.Number.Hex:           '#009999',
        Literal.Number.Integer:       '#009999',
        Literal.Number.Oct:           '#009999',
        Literal.String.Backtick:      '#d01040',
        Literal.String.Char:          '#d01040',
        Literal.String.Doc:           '#d01040',
        Literal.String.Double:        '#d01040',
        Literal.String.Escape:        '#d01040',
        Literal.String.Heredoc:       '#d01040',
        Literal.String.Interpol:      '#d01040',
        Literal.String.Other:         '#d01040',
        Literal.String.Regex:         '#009926',
        Literal.String.Single:        '#d01040',
        Literal.String.Symbol:        '#990073',
        Name.Builtin.Pseudo:          '#004380 italic bold',
        Name.Variable.Class:          '#008080',
        Name.Variable.Global:         '#008080',
        Name.Variable.Instance:       '#008080',
        Literal.Number.Integer.Long:  '#009999'
    }
