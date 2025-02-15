from .nodes import NumberNode, DecimalNode, BoolNode, IdAccessNode, IntAssignNode, FloatAssignNode, BoolAssignNode, ArithOpNode, UnaryOpNode
from .tokentypes import TT_ID, TT_ASSIGN, TT_INT, TT_FLOAT, TT_BOOL, TT_PLUS, TT_MINUS, TT_MUL, TT_DIV, TT_INTDIV, TT_EXPO, TT_MOD, TT_GREATER, TT_LESS, TT_GREATEREQUAL, TT_LESSEQUAL, TT_EQUALTO, TT_NOTEQUAL, TT_NOT, TT_AND, TT_OR, TT_DTYPE, TT_LPAREN, TT_RPAREN, TT_EOF
from .errors import InvalidSyntaxError

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_idx = -1
        self.advance()

    def advance(self):
        self.token_idx += 1
        if self.token_idx < len(self.tokens):
            self.current_tok = self.tokens[self.token_idx]
        return self.current_tok

    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Error")) # TODO: figure out what error message should be here
        return res

    # Production Rules
    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected a closing symbol ')'"))
            
        elif tok.type == TT_INT:
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(tok))
        
        elif tok.type == TT_FLOAT:
            res.register_advancement()
            self.advance()
            return res.success(DecimalNode(tok))

        elif tok.type == TT_ID:
            res.register_advancement()
            self.advance()
            return res.success(IdAccessNode(tok))
        
        elif tok.type == TT_BOOL:
            res.register_advancement
            self.advance()
            return res.success(BoolNode(tok))
        
        return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected int, float, identifier, '+', '-' or '('"))
            
    def power(self):
        return self.arith_op(self.atom, (TT_EXPO, ), self.factor)

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(tok, factor))
        
        return self.power()

    def term(self):
        return self.arith_op(self.factor, (TT_MUL, TT_DIV))

    def arith_expr(self):
        return self.arith_op(self.term, (TT_PLUS, TT_MINUS))

    def rel_expr(self):
        res = ParseResult()

        if self.current_tok.type == TT_NOT:
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            node = res.register(self.rel_expr())
            if res.error: return res
            return res.success(UnaryOpNode(op_tok, node))
        
        node = res.register(self.arith_op(self.arith_expr, (TT_GREATER, TT_LESS, TT_GREATEREQUAL, TT_LESSEQUAL, TT_EQUALTO, TT_NOTEQUAL)))

        if res.error:
            return res.failure(InvalidSyntaxError(
                               self.current_tok.pos_start, self.current_tok.pos_end,
                               "Expected int, float, identifier, '+', '-', '(', 'not', or 'NOT'"))
        
        return res.success(node)

    def expr(self):
        res = ParseResult()

        # num identifier = expr
        if self.current_tok.matches(TT_DTYPE, 'num') or self.current_tok.matches(TT_DTYPE, 'number'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_ID:
                res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected an identifier"
                ))

            var_name = self.current_tok
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_ASSIGN:
                res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))

            res.register_advancement()
            self.advance()

            #? Kung i automatic parse ba kapag float tok nakuha or hindi nalang tatanggapin as in?

            if self.current_tok.type != TT_INT:
                res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected int"
                ))
            expr = res.register(self.expr())
            res.register_advancement()
            self.advance()
            if res.error: return res
            return res.success(IntAssignNode(var_name, expr))
        
        # decimal identifier = 1.9
        if self.current_tok.matches(TT_DTYPE, 'deci') or self.current_tok.matches(TT_DTYPE, 'decimal'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_ID:
                res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected an identifier"
                ))

            var_name = self.current_tok
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_ASSIGN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))
   
            res.register_advancement()
            self.advance()

            # parsing int to float
            if self.current_tok.type == TT_INT:
                self.current_tok.type = TT_FLOAT
                self.current_tok.value = float(self.current_tok.value)

            if self.current_tok.type != TT_FLOAT:
                res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected int or float"
                ))
            expr = res.register(self.expr())
            res.register_advancement()
            self.advance()
            if res.error: return res
            return res.success(FloatAssignNode(var_name, expr))
        
        # boolean identifier = bool
        if self.current_tok.matches(TT_DTYPE, 'bool') or self.current_tok.matches(TT_DTYPE, 'boolean'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_ID:
                res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected an identifier"
                ))

            var_name = self.current_tok
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_ASSIGN:
                res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))

            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_BOOL:
                res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected true, or false"
                ))

            expr = res.register(self.expr())
            res.register_advancement()
            self.advance()
            if res.error: return res
            return res.success(BoolAssignNode(var_name, expr))
        
        node = res.register(self.arith_op(self.rel_expr, (TT_AND, TT_OR)))

        if res.error:
            return res.failure(InvalidSyntaxError(
                               self.current_tok.pos_start, self.current_tok.pos_end,
                               "Expected a data type keyword, int, float, identifier, '+', '-', '(', 'not', or 'NOT'"))
        
        return res.success(node)

    def arith_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a

        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res

        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = ArithOpNode(left, op_tok, right)

        return res.success(left)
    

# Parse Result
class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0

    def register_advancement(self):
        self.advance_count += 1

    def register(self, res):
        self.advance_count += res.advance_count
        if res.error: self.error = res.error
        return res.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self
