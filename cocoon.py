# CONSTANTS

DIGITS = '0123456789'
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
WHITESPACES = ' \t\n\v\r'
OPERATORS = '+-/*^%'
RELATIONAL = '=!><'
PUNCTUATIONS = '()[]'
KEYWORDS = {"true", "false", "number", "num", "decimal", "deci", "text", "character", "char", "boolean", "bool", "done", "next", "give", "group", "build"}

# ERRORS

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
    
    def as_string(self):
        result = f'{self.error_name}: {self.details}'
        result += f'\nFile {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        return result
    
class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)

class IllegalIdentifierError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Identifier', details)

class IllegalNumberError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Number', details)

class SyntaxError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Syntax Error', details)

# POSITION

class Position:
    def __init__(self, idx, ln, col, fn, ftext):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftext = ftext

    def advance(self, current_char):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0
 
        return self
    
    def stepback(self, current_char):
        self.idx -= 1
        self.col -= 1

        if current_char == '\n':
            self.ln -=1
            previousNLidx = self.ftext.rfind('\n')

            if previousNLidx != -1:
                self.col = (self.idx - previousNLidx) - 1
            else:
                self.col = self.idx

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftext)

# TOKENS (TT means token type)

TT_INT = 'Number'
TT_FLOAT = 'Decimal'
TT_STR = 'Text'
TT_BOOL = 'Bool'
TT_LPAREN = 'Left_Paren'
TT_RPAREN = 'Right_Paren'
TT_LSQUARE = 'Left_Square'
TT_RSQUARE = 'Right_Square'
TT_COMMA = 'Comma'
TT_SEMICOLON = 'Semicolon'
TT_ASSIGN = 'Assignment_Operator'
TT_OP = 'Arithmetic_Operator'
TT_UNARY = 'Unary_Operator'
TT_REL = 'Relational_Boolean'
TT_LOG = 'Logical_Boolean'
TT_RWORD = 'Reserved_Word'
TT_ID = 'Identifier'

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'

# LEXER

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def stepback(self):
        self.pos.stepback(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def check(self):
        self.advance()
        char = self.current_char
        self.stepback()
        return char

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in WHITESPACES:
                self.advance()
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char in ALPHABET + '_':
                result = self.make_identifier()
                if isinstance(result, Token):
                    tokens.append(result)
                elif isinstance(result, Error):
                    return [], result
            elif self.current_char in DIGITS:
                result = self.make_number()
                if isinstance(result, Token):
                    tokens.append(result)
                elif isinstance(result, Error):
                    return [], result
            elif self.current_char in PUNCTUATIONS:
                tokens.append(self.make_punctuation())
                self.advance()
            elif self.current_char == '=':
                tokens.append(Token(TT_ASSIGN))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")

        return tokens, None
    
    def make_punctuation(self):
        if self.current_char in PUNCTUATIONS:
            if self.current_char == '(':
                return Token(TT_LPAREN)
            elif self.current_char == ')':
                return Token(TT_RPAREN)
            elif self.current_char == '[':
                return Token(TT_LSQUARE)
            elif self.current_char == ']':
                return Token(TT_RSQUARE)
            elif self.current_char == ',':
                return Token(TT_COMMA)
            elif self.current_char == ':':
                return Token(TT_SEMICOLON)

    def make_identifier(self):
        id_str = ''

        while self.current_char != None and self.current_char in ALPHABET + DIGITS + WHITESPACES + '_':
            if self.current_char in WHITESPACES:
                break
            else:
                id_str += self.current_char
            self.advance()

        if id_str in KEYWORDS:
            return Token(TT_RWORD, id_str)
        else:
            return Token(TT_ID, id_str)
    
    def make_string(self):
        text_str = ''
        q_count = 0

        while self.current_char != None and self.current_char in ALPHABET + WHITESPACES + '"':
            if self.current_char == '"':
                if q_count == 2:
                    break
                q_count += 1
                text_str += '"'
            else:
                text_str += self.current_char
            self.advance()

        return Token(TT_STR, text_str)

    def make_number(self):
        num_str = ''
        dot_count = 0
        isValid = True
        isIdentifier = False
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + ALPHABET + WHITESPACES + '.':
            check = self.check()
            if self.current_char in WHITESPACES:
                    break
            elif self.current_char in ALPHABET:
                isValid = False
                num_str += self.current_char
            elif (not num_str and self.current_char in DIGITS) and check in ALPHABET:
                isIdentifier = True
                num_str += self.current_char
            elif self.current_char == '.':
                if dot_count == 1:
                    dot_count += 1
                    break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0 and isValid == True:
            return Token(TT_INT, int(num_str))
        elif dot_count == 2 and isValid == True:
            return SyntaxError(pos_start, self.pos, f'{num_str}')
        elif isIdentifier:
            return IllegalIdentifierError(pos_start, self.pos, f'{num_str}')
        elif isValid == False:
            return IllegalNumberError(pos_start, self.pos, f'{num_str}')
        else:
            return Token(TT_FLOAT, float(num_str))

# RUN

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    return tokens, error