import antlr4

from bones.ts._type_lang.TypeLangLexer import TypeLangLexer
from bones.ts._type_lang.TypeLangParser import TypeLangParser



def parse(stream):
    l = TypeLangLexer(stream)
    stream = antlr4.CommonTokenStream(l)
    p = TypeLangParser(stream)
    tree = p.tl_body()

    w = antlr4.ParseTreeWalker()
    listener = Listener()
    w.walk(listener, tree)

    print(tree)
    print(tree.toStringTree(recog=p))



class Listener:
    def visitTerminal(self, node: antlr4.TerminalNode): pass
    def visitErrorNode(self, node: antlr4.ErrorNode):
        print(f'error: {node}')
        1/0
    def enterEveryRule(self, ctx: antlr4.ParserRuleContext): pass
    def exitEveryRule(self, ctx: antlr4. ParserRuleContext):
        if (fn := globals().get(f'{ctxName(ctx)}')): fn(ctx)


def define_atom(ctx):
    print(_atom_expr(ctx.atom_))

def define_expr(ctx):
    print(_expr(ctx.expr_))

def return_expr(ctx):
    print(_expr(ctx.expr_))


def get(ctx):
    name = ctxName(ctx)
    if name == 'name':          return ctx.name_.text
    if name == 'assign_atom2':  return f'({_atom_expr(ctx.atom_)})'


def _atom_expr(ctx):
    name = ctxName(ctx)
    if name == 'new_atom_multi':        return f'{ctx.name_.text} :: atom'
    if name == 'new_atom':              return f'{ctx.name_.text} :: atom'
    if name == 'new_atom_in':           return f'{ctx.name_.text} :: atom in {get(ctx.atom_)}'
    if name == 'new_atom_explicit':     return f'{ctx.name_.text} :: atom explicitly matched'
    if name == 'new_atom_explicit_in':  return f'{ctx.name_.text} :: atom in {get(ctx.atom_)} explicitly matched'
    if name == 'new_atom_implicitly':   return f'{ctx.name_.text} :: atom implicity implying {get(ctx.atom_)}'
    return f'\nunhandled atom expr: {name}'

def _expr(ctx):
    msg = _expr_imp(ctx)
    while msg.startswith('(') and msg.endswith(')'):
        msg = msg[1:-1]
    return msg

def _expr_imp(ctx):
    name = ctxName(ctx)

    # assign_expr_imp rule
    if name == 'explicit_expr':     return f'{ctx.name_.text} <= {_expr(ctx.expr_)} exp'
    if name == 'assign_expr_to':    return f'{ctx.name_.text} <= {_expr(ctx.expr_)}'
    if name == 'prealloc':          return f'#define {ctx.name_.text}'

    # _expr rule
    if name == 'inter':         return f'({_expr_imp(ctx.lhs_)} & {_expr_imp(ctx.rhs_)})'
    if name == 'union':         return f'({_expr_imp(ctx.lhs_)} + {_expr_imp(ctx.rhs_)})'
    if name == 'tuple':         return f'({_expr_imp(ctx.lhs_)} * {_expr_imp(ctx.rhs_)})'
    if name == 'struct':        return f'{{{", ".join(_getFields(ctx.fields_))}}}'
    if name == 'rec':           return f'{{{{{", ".join(_getFields(ctx.fields_))}}}}}'
    if name == 'seq':           return f'({_expr_imp(ctx.lhs_)} ** {_expr_imp(ctx.rhs_)})'
    if name == 'map':           return f'({_expr_imp(ctx.lhs_)} ** {_expr_imp(ctx.rhs_)})'
    if name == 'fn':            return f'({_expr_imp(ctx.lhs_)} ^ {_expr_imp(ctx.rhs_)})'
    if name == 'inter_low':     return f'(({_expr(ctx.lhs_)}) & {_expr_imp(ctx.rhs_)})'
    if name == 'name_or_atom':  return get(ctx.name_or_atom_)
    if name == 'expr_parens':   return f'{_expr_imp(ctx.expr_)}'
    if name == 'seq_var':       return f'{_expr_imp(ctx.name_)}'
    if name == 'mut_name':      return f'*{ctx.name_.text}'
    
    if name == 'CommonToken':   return ctx.text
    return f'\nunhandled expr: {name}'

def _getFields(ctx):
    fields = [_field(ctx)]
    while ctx.rhs_:
        fields.append(_field(ctx.rhs_))
        ctx = ctx.rhs_
    return fields

def _field(ctx):
    return f'{_expr_imp(ctx.name_)}={_expr_imp(ctx.type_)}'


def ctxName(ctx):
    name = type(ctx).__name__
    if name.endswith('Context'): name = name[:-7].lower()
    return name

