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
from pygments.lexers.web import CoffeeScriptLexer
from pygments.lexers.templates import ErbLexer
from pygments.token import Token, Text, Keyword, Name, Comment, String, Error, Number, Operator, Generic, Literal, Punctuation

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

    lookahead = 10
    lookbehind = 1
    queue = collections.deque()
    nows_queue = collections.deque()
    processed = collections.deque([], lookbehind)

    def peek_ahead(self, n):
        if len(self.nows_queue) >= n:
            return self.nows_queue[n-1]
        else:
            return (None, None, None)

    def next(self):
        return self.peek_ahead(1)

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
            if token is not Token.Text:
                self.nows_queue.append((index, token, value))
            if len(self.nows_queue) < 1 + self.lookahead: continue
            curr = self.queue.popleft()
            if _token(curr) is not Token.Text:
                self.nows_queue.popleft()
            ans = __process(self.process_one(curr))
            if ans is not None:
                yield ans

        while (len(self.queue) > 0):
            curr = self.queue.popleft()
            if _token(curr) is not Token.Text:
                self.nows_queue.popleft()
            ans = __process(self.process_one(curr))
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
class Ruby193Lexer(RedLexerBase):
    name = 'Ruby193'
    aliases = ['ruby193']
    filenames = ['*.rb'] # just to have one if you whant to use

    tokens = {}
    tokens.update(RubyLexer.tokens)

    string_rules = tokens['strings']
    string_rules[4] = (r'([a-zA-Z_][a-zA-Z0-9_]*)(:)(?!:)', bygroups(String.Symbol, Token.Punctuation))

    def process_one(self, curr):
        curr_idx, curr_token, curr_value = curr

        # remove weird lexing rule that says that "name" is a buildin keyword
        if curr_value == "name" and curr_token is Name.Builtin and _token(self.next()) is Token.Punctuation:
            return (curr_idx, Literal.String.Symbol, curr_value)

        if curr_value in ["p", "sub"] and curr_token is Name.Builtin:
            nt = self.next()
            if _token(nt) is Token.Punctuation and _value(nt) == ":":
                return (curr_idx, Literal.String.Symbol, curr_value)
            else:
                return (curr_idx, Name, curr_value)

        return curr

"""
--------------------------------------------------------------------------------
(1) Adds new keywords

(2) Converts tokens following class generating keywords in Red from
    Name.Constant to Name.Class

--------------------------------------------------------------------------------
"""
class ARbyLexer(Ruby193Lexer):
    name = 'ARby'
    aliases = ['arby']
    filenames = ['*.arby'] # just to have one if you whant to use

    CLASS_GEN_KEYWORDS = ['sig', 'abstract', 'alloy_model', 'alloy_module', 'alloy', 'enum']
    OPS_KEYWORDS = ['extends', 'set', 'seq', 'one', 'lone', 'no', 'all', 'some', 'exist']
    FUN_KEYWORDS = ['fun', 'pred', 'assertion', 'fact', 'check', 'run', 'this', 'not_in?', 'in?', 'open', 'solve', 'procedure', 'inst',
                    'exactly', 'ordered', 'iden', 'univ', 'let', 'one_one', 'one_lone', 'lone_one', 'lone_one']

    EXTRA_KEYWORDS = CLASS_GEN_KEYWORDS + OPS_KEYWORDS + FUN_KEYWORDS

    tokens = {}
    tokens.update(Ruby193Lexer.tokens)

    def to_conv_to_sym(self):
        ans = []
        if hasattr(self, "my_to_conv_to_sym"):
            ans = self.my_to_conv_to_sym
        else:
            self.my_to_conv_to_sym = []
        return ans

    def process_one(self, curr):
        curr_idx, curr_token, curr_value = curr

        # convert Name tokens to Keyword for extra Red keywobrds
        if curr_value in self.EXTRA_KEYWORDS:
            return (curr_idx, Keyword, curr_value)

        # convert Name.Constant tokens to Name.Class for names following Red class generating keywords
        prev_token = _token(self.prev())
        prev_is_keyword = (prev_token is Keyword) or (prev_token is Keyword.Pseudo)
        prev_is_red_keyword = prev_is_keyword and _value(self.prev()) in self.CLASS_GEN_KEYWORDS
        if curr_token is Name.Constant and prev_is_red_keyword:
            return (curr_idx, Name.Class, curr_value)

        # convert braces to Operator to make them bold
        if curr_value in ['{', '}'] and curr_token is Token.Punctuation:
            return (curr_idx, Operator, curr_value)

        # convert named variables to simbols when preceeded by "[" and followed by ","
        if curr in self.to_conv_to_sym():
            return (curr_idx, Literal.String.Symbol, curr_value)
        elif curr_token is Name and (_value(self.prev()) in ["[", "("]): 
            nx = 1
            yes = False
            while(1):
                #import pdb; pdb.set_trace()
                if _value(self.peek_ahead(nx)) == ",":
                    nextnext = self.peek_ahead(nx+1)
                    if _token(nextnext) is Literal.String.Symbol:
                        yes = True
                        break
                    else:
                        self.to_conv_to_sym().append(nextnext)
                        nx = nx + 2
                else:
                    yes = False
                    del self.to_conv_to_sym()[:]
                    break
            if yes:
                return (curr_idx, Literal.String.Symbol, curr_value)

        return Ruby193Lexer.process_one(self, curr)

"""
--------------------------------------------------------------------------------
(1) Adds new keywords

(2) Emphasize certain Red builtin functions (e.g., 'render')
--------------------------------------------------------------------------------
"""
class RedLexer(ARbyLexer):
    name = 'Red'
    aliases = ['red']
    filenames = ['*.red'] # just to have one if you whant to use

    CLASS_GEN_KEYWORDS = ['abstract_record', 'abstract_machine', 'record', 'machine', 'event', 'policy']
    RED_KEYWORDS = ['requires', 'ensures', 'from', 'to', 'params', 'principal', 'restrict', 'refs', 'owns', 'fields', 'success_note', 'error_note', 'global', 'write', 'filter', 'read']
    EXTRA_KEYWORDS = CLASS_GEN_KEYWORDS + RED_KEYWORDS + ARbyLexer.OPS_KEYWORDS

    EMPH_STRONG_FUNCS = ['render']
    EMPH_FUNCS = ['reject', 'unless', 'when']

    tokens = {}
    tokens.update(ARbyLexer.tokens)

    def process_one(self, curr):
        curr_idx, curr_token, curr_value = curr

        # convert Name tokens to Name.Builtin.Pseudo for emphasized Red functions
        if curr_token is Name and curr_value in self.EMPH_STRONG_FUNCS:
            return (curr_idx, Keyword.Pseudo, curr_value)

        # convert Name tokens to Name.Builtin.Pseudo for emphasized Red functions
        if curr_token is Name and curr_value in self.EMPH_FUNCS:
            return (curr_idx, Name.Builtin.Pseudo, curr_value)

        return ARbyLexer.process_one(self, curr)

class SunnyLexer(RedLexerBase):
    name = 'Sunny'
    aliases = ['sunny']
    filenames = ['*.sunny'] # just to have one if you whant to use

    CLASS_GEN_KEYWORDS = ['record', 'abstract', 'event', 'machine', 'user', 'client', 'server']
    FUN_KEYWORDS = ['simport', 'requires', 'ensures', 'from', 'to', 'params', 'set', 'compose'] 
                      # 'fun', 'pred', 'assertion', 'fact', 'check', 'run', 'this', 'not_in?', 'in?', 'open', 
                      # 'solve', 'procedure', 'inst', 'exactly', 'ordered', 'iden', 'univ', 'let', 'one_one', 
                      # 'one_lone', 'lone_one', 'lone_one']
    
    EXTRA_KEYWORDS = CLASS_GEN_KEYWORDS + FUN_KEYWORDS

    tokens = {}
    tokens.update(CoffeeScriptLexer.tokens)

    def process_one(self, curr):
        curr_idx, curr_token, curr_value = curr

        if curr_value in self.EXTRA_KEYWORDS:
            return (curr_idx, Keyword, curr_value)

        return curr

"""
--------------------------------------------------------------------------------
(1) Adds new keywords
--------------------------------------------------------------------------------
"""
class SlangLexer(ARbyLexer):
    name = 'Slang'
    aliases = ['slang']
    filenames = ['*.sarb'] # just to have one if you whant to use

    CLASS_GEN_KEYWORDS = ['view', 'component', 'data', 'trusted', 'abstract', 'model',
                          'critical', 'operation']
    SLANG_KEYWORDS = ['creates', 'guard', 'dynamic', 'effects', 'sends', 'triggers', 'response']
    STRONG_FUNCS = ['critical', 'trusted']
    
    EXTRA_KEYWORDS = CLASS_GEN_KEYWORDS + ARbyLexer.OPS_KEYWORDS

    tokens = {}
    tokens.update(ARbyLexer.tokens)

    def process_one(self, curr):
        curr_idx, curr_token, curr_value = curr

        # convert Name tokens to Name.Function for emphasized functions
        if curr_token is Name and curr_value in self.STRONG_FUNCS:
            return (curr_idx, Name.Function, curr_value)

        # convert Name tokens to Name.Function for SLANG_KEYWORDS
        if curr_token is Name and curr_value in self.SLANG_KEYWORDS:
            return (curr_idx, Generic.Inserted, curr_value)

        return ARbyLexer.process_one(self, curr)



"""
--------------------------------------------------------------------------------
Like ERB except that it uses Ruby193Lexer for ruby expressions
--------------------------------------------------------------------------------
"""
class ErrbLexer(ErbLexer):
    name = 'ERRB'
    aliases = ['erb', 'errb']
    mimetypes = ['application/x-ruby-templating']
    def __init__(self, **options):
        ErbLexer.__init__(self, **options)
        self.ruby_lexer = Ruby193Lexer(**options)

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

    comment_color = '#8f5902' #'#777766'

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
        Keyword.Pseudo:               '#008080 bold',
        Keyword.Reserved:             '#000000 bold',
        Keyword.Type:                 '#445588 bold',
        Literal.Number:               '#009999',
        Literal.String:               '#d01040',
        Name.Attribute:               '#008080',
        Name.Builtin:                 '#0086B3',
        Name.Class:                   '#445588 bold',
        Name.Constant:                '#008080',
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
        Name.Builtin.Pseudo:          '#999999',
        Name.Variable.Class:          '#008080',
        Name.Variable.Global:         '#008080',
        Name.Variable.Instance:       '#008080',
        Literal.Number.Integer.Long:  '#009999'
    }

class GithubCustom1Style(Style):
    default_style = ""

    comment_color = '#8f5902' #'#777766'

    styles = {}
    styles.update(GithubStyle.styles)
    styles.update({
        Comment:                      comment_color + ' italic',
        Comment.Multiline:            comment_color + ' italic',
        Comment.Preproc:              comment_color + ' bold italic',
        Comment.Single:               comment_color + ' italic',
        Comment.Special:              comment_color + ' bold italic',
        Name.Constant:                '#008080', #'#445588', # '#004380', 
        Name.Builtin.Pseudo:          '#004380 italic',
        Keyword.Pseudo:               '#004380 italic bold'
    })
