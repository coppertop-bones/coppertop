# **********************************************************************************************************************
# Copyright (c) 2025 David Briant. All rights reserved.
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
# **********************************************************************************************************************

# OPEN: currently we put the responsibility for handling recursive definitions into the eval function of the AST Nodes
#       (especially set and inter nodes). It may be more scalable to handle this in the typemanager, but in Python,
#       this would mean any type that can morph from a recursive type would need to be of the same class as the
#       recursive type since syntactically implicit recursion is no detectable.
#           GBP: recursive
#           t1: (ccy & GBP) in ccy
#           GBP: t1

import antlr4

from bones.lang._type_lang.utils import ctxLabel

from bones.core.sentinels import Missing
from bones.core.errors import ProgrammerError, NotYetImplemented


class SrcLoc:
    __slots__ = ['l1', 'l2', 's1', 's2']
    def __init__(self, ctx):
        if ctx.__class__.__name__ == 'CommonToken':
            self.l1 = ctx.line
            self.l2 = ctx.line
            self.s1 = ctx.start
            self.s2 = ctx.stop
        else:
            self.l1 = ctx.start.line
            self.l2 = ctx.stop.line
            self.s1 = ctx.start.start
            self.s2 = ctx.stop.stop


# AST Nodes

class TLNode:
    __slots__ = ['loc']
    def __init__(self, loc):
        self.loc = loc
    def eval(self, tm):
        raise NotImplementedError()


class Get(TLNode):
    __slots__ = ['varname']
    def __init__(self, varname, loc):
        super().__init__(loc)
        self.varname = varname
    def eval(self, tm, parent):
        return tm.get(self.varname)
    def __repr__(self):
        return f'Get(\'{self.varname}\')'


class Set(TLNode):
    __slots__ = ['varname', 'expr_or_atom']
    def __init__(self, varname, expr_or_atom, loc):
        super().__init__(loc)
        self.varname = varname
        self.expr_or_atom = expr_or_atom
    def eval(self, tm, parent):
        with tm.onErrRollback():
            # if isinstance(self.expr_or_atom, Atom):
            #     # OPEN: why????
            #     btype = self.expr_or_atom.eval(tm, self)
            btype = self.expr_or_atom.eval(tm, self)
            tm.set(self.varname, btype)
        return btype
    def __repr__(self):
        return f'Set(\'{self.varname}\')'


class Atom(TLNode):
    __slots__ = ['explicit', 'space', 'implicitly', 'varname']
    def __init__(self, explicit, space, implicitly, varname, loc):
        super().__init__(loc)
        self.explicit = explicit
        self.space = space
        self.implicitly = implicitly
        self.varname = varname
    def eval(self, tm, parent):
        return tm.atom(self.explicit, self.space, self.implicitly, self.varname)


class Recursive(TLNode):
    __slots__ = ['main', 'space']
    def __init__(self, space, loc):
        super().__init__(loc)
        self.main = Missing
        self.space = space
    def eval(self, tm, parent):
        return tm.recursive(self.space.eval(tm, self) if self.space else Missing)


class Mutable(TLNode):
    __slots__ = ['contained']
    def __init__(self, contained, loc):
        super().__init__(loc)
        self.contained = contained
    def eval(self, tm, parent):
        return self.contained.eval(tm, self)


class Inter(TLNode):
    __slots__ = ['types', 'space']
    def __init__(self, types, space, loc):
        super().__init__(loc)
        self.types = types
        self.space = space
    def eval(self, tm, parent):
        types = [t.eval(tm, self) for t in self.types]
        id = Missing
        if isinstance(parent, Set):
            # handle recursive type assignment here
            if id := tm._idByVarname.get(parent.varname, Missing):
                if isinstance(btype := tm._btypeById.get(id, Missing), Recursive):
                    id = btype.id
        return tm.inter(types, self.space.eval(tm, self) if self.space else Missing, id)
    def __repr__(self):
        return f'InterIn()' if self.space else f'Inter()'


class Expr(TLNode):
    __slots__ = ['op', 'args']
    def __init__(self, op, args, loc):
        super().__init__(loc)
        self.op = op
        self.args = args
    def eval(self, tm, parent):
        if self.op == 'struct':
            return tm.struct(tuple([(field, t.eval(tm, self)) for field, t in self.args]))
        elif self.op == 'rec':
            return tm.rec(tuple([(field, t.eval(tm, self)) for field, t in self.args]))
        else:
            args = tuple([t.eval(tm, self) for t in self.args])
            if self.op == 'union':
                return tm.union(args)
            elif self.op == 'tuple':
                return tm.tuple(args)
            elif self.op == 'seq':
                return tm.seq(args)
            elif self.op == 'map':
                return tm.map(args)
            elif self.op == 'fn':
                return tm.fn(tuple(args))
            else:
                raise ValueError(f'Unknown op: {self.op}')
    def __repr__(self):
        return f'Expr(\'{self.op}\')'


class CheckImplicitRecursiveAssigned(TLNode):
    __slots__ = []
    def __init__(self, loc):
        super().__init__(loc)
    def eval(self, tm, parent):
        return tm.checkImplicitRecursiveAssigned()
    def __repr__(self):
        return f'CheckImplicitRecursiveAssigned()'


class Return(TLNode):
    __slots__ = ['_expr']
    def __init__(self, expr, loc):
        super().__init__(loc)
        self._expr = expr
    def eval(self, tm, parent):
        answer = self._expr.eval(tm, self)
        tm.done()
        return answer
    def __repr__(self):
        return f'Return()'


class Done(TLNode):
    __slots__ = []
    def __init__(self, loc):
        super().__init__(loc)
    def eval(self, tm, parent):
        return tm.done()
    def __repr__(self):
        return f'Return()'



class TypeLangAstBuilder:
    __slots__ = ['_nodeByCtx', '_last', 'ast', 'debug']

    def __init__(self):
        self._nodeByCtx = {}
        self._last = Missing
        self.ast = []
        self.debug = False

    def visitTerminal(self, node: antlr4.TerminalNode): pass
    def visitErrorNode(self, node: antlr4.ErrorNode):
        print(f'error: {node}')
        1/0
    def enterEveryRule(self, ctx: antlr4.ParserRuleContext): pass
    def exitEveryRule(self, ctx: antlr4. ParserRuleContext):
        label = ctxLabel(ctx)
        if self.debug: print(label)
        if (fn := getattr(self, label, Missing)):
            fn(ctx)
        elif label.startswith('ignore'):
            pass
        else:
            raise ProgrammerError(f'Handler for "{label}" not defined')


    # RULES

    def assign_expr_to(self, ctx):
        self.ast.append(
            Set(
                ctx.name_.text,
                self._nodeByCtx[ctx.expr_],
                SrcLoc(ctx)
            )
        )
        self._nodeByCtx[ctx] = self.ast[-1]
        self.ast.append(
            CheckImplicitRecursiveAssigned(SrcLoc(ctx))
        )

    def atom(self, ctx):
        self._assign_atom(ctx.name_.text, False, Missing, Missing, ctx)

    def atom_explicit(self, ctx):
        self._assign_atom(ctx.name_.text, True, Missing, Missing, ctx)

    def atom_explicit_in(self, ctx):
        self._assign_atom(ctx.name_.text, True, self.get(ctx.atom_), Missing, ctx)

    def atom_implicitly(self, ctx):
        self._assign_atom(ctx.name_.text, False, Missing, self.get(ctx.atom_), ctx)

    def atom_in(self, ctx):
        self._assign_atom(ctx.name_.text, False, self.get(ctx.atom_), Missing, ctx)

    def atom_in_parens(self, ctx):
        pass

    def atom_multi(self, ctx):
        rhs = self._rootAtomContext(ctx)
        label = ctxLabel(rhs)
        if label == 'atom':
            return self._assign_atom(ctx.name_.text, False, Missing, Missing, ctx)
        if label == 'atom_in':
            return self._assign_atom(ctx.name_.text, False, self.get(rhs.atom_), Missing, ctx)
        else:
            raise NotYetImplemented(label)

    def comment(self, ctx):
        if ctx.comment_.text == '// error':
            print(ctx.text)

    def check_all_consumed(self, ctx):
        if ctx.children:
            children = [e.symbol.text for e in ctx.children]
            print(f'\nUnconsumed tokens:\n{children}')
            raise SyntaxError()

    def done(self, ctx):
        self.ast.append(Done(SrcLoc(ctx)))

    def expr_in(self, ctx):
        interCtx = ctx.expr_
        while ctxLabel(interCtx) == 'expr_paren':
            interCtx = interCtx.expr_
        if ctxLabel(interCtx) in ('inter', 'inter_high', 'inter_low'):
            inter = self._nodeByCtx[interCtx]
            inter.space = self.get(ctx.atom_)
            self._nodeByCtx[ctx] = inter
        else:
            raise Exception('only intersections, recursive intersections or atoms can be "in" a space')

    def expr_parens(self, ctx):
        pass

    def fn(self, ctx):
        tArgs = self._getNode(ctx.lhs_)
        tRet = self._getNode(ctx.rhs_)
        self._nodeByCtx[ctx] = n = Expr('fn', (tArgs, tRet), SrcLoc(ctx))
        return n

    def get(self, ctx):
        label = ctxLabel(ctx)
        if label == 'name':
            return Get(ctx.name_.text, SrcLoc(ctx))
        elif label == 'atom_in_parens':
            return self._nodeByCtx[ctx.atom_]
        else:
            raise ProgrammerError(f'Unknown label "{label}" in get')

    def inter(self, ctx):
        parentLabel = ctxLabel(ctx.parentCtx)
        if parentLabel in ('inter', 'inter_low'): return Missing    # defer creation of the intersection to parent
        types = tuple(self._collectInters([], ctx))
        self._nodeByCtx[ctx] = n = Inter(types, Missing, SrcLoc(ctx))
        return n

    def inter_high(self, ctx):
        parentLabel = ctxLabel(ctx.parentCtx)
        if parentLabel == 'inter_high': return Missing              # defer creation of the intersection to parent
        types = tuple(self._collectInterHighs([], ctx))
        self._nodeByCtx[ctx] = n = Inter(types, Missing, SrcLoc(ctx))
        return n

    def inter_low(self, ctx):
        return self.inter(ctx)

    def map(self, ctx):
        self._nodeByCtx[ctx] = n = Expr('map', [self._getNode(ctx.lhs_), self._getNode(ctx.rhs_)], SrcLoc(ctx))
        return n

    def mutable(self, ctx):
        self._nodeByCtx[ctx] = n = Mutable(self._getNode(ctx.expr_), SrcLoc(ctx))
        return n

    def name(self, ctx):
        pass

    def name_or_atom(self, ctx):
        pass

    def prealloc(self, ctx):
        self.ast.append(
            Set(
                ctx.name_.text,
                Recursive(Missing, SrcLoc(ctx)),
                SrcLoc(ctx)
            )
        )
        self._nodeByCtx[ctx] = self.ast[-1]

    def prealloc_in(self, ctx):
        self.ast.append(
            Set(
                ctx.name_.text,
                Recursive(self.get(ctx._atom), SrcLoc(ctx)),
                SrcLoc(ctx)
            )
        )
        self._nodeByCtx[ctx] = self.ast[-1]

    def rec(self, ctx):
        fields = tuple(self._collectFields([], ctx.fields_))
        self._nodeByCtx[ctx] = n = Expr('rec', fields, SrcLoc(ctx))
        return n

    def return_expr(self, ctx):
        self.ast.append(Return(self._getNode(ctx.expr_), SrcLoc(ctx)))

    def return_named(self, ctx):
        self.ast.append(Return(self._getNode(ctx.atom_), SrcLoc(ctx)))

    def schema_var(self, ctx):
        return Get(ctx.name_.text, SrcLoc(ctx))

    def seq(self, ctx):
        self._nodeByCtx[ctx] = n = Expr('seq', [self._getNode(ctx.rhs_)], SrcLoc(ctx))
        return n

    def struct(self, ctx):
        fields = tuple(self._collectFields([], ctx.fields_))
        self._nodeByCtx[ctx] = n = Expr('struct', fields, SrcLoc(ctx))
        return n

    def tuple(self, ctx):
        types = tuple(self._collectTuples([], ctx))
        self._nodeByCtx[ctx] = n = Expr('tuple', types, SrcLoc(ctx))
        return n

    def union(self, ctx):
        parentLabel = ctxLabel(ctx.parentCtx)
        if parentLabel == 'union': return Missing      # defer creation of the intersection to parent
        types = tuple(self._collectUnions([], ctx))
        self._nodeByCtx[ctx] = n = Expr('union', types, SrcLoc(ctx))
        return n



    # UTILITIES

    def _getNode(self, ctx):
        if (node := self._nodeByCtx.get(ctx)): return node
        label = ctxLabel(ctx)
        if label == 'inter_high':   return self.inter(ctx)
        if label == 'inter':        return self.inter(ctx)
        if label == 'union':        return self.union(ctx)
        if label == 'tuple':        return self.tuple(ctx)
        if label == 'struct':       return self.struct(ctx)
        if label == 'rec':          return self.rec(ctx)
        if label == 'seq':          return self.seq(ctx)
        if label == 'map':          return self.map(ctx)
        if label == 'fn':           return self.fn(ctx)
        if label == 'schema_var':   return self.schema_var(ctx)
        if label == 'name_or_atom': return self.get(ctx.name_or_atom_)
        if label == 'expr_parens':  return self._getNode(ctx.expr_)
        if label == 'mutable':      return self.mutable(ctx)
        if label == 'atom_in_parens': return self._getNode(ctx.atom_)
        raise ProgrammerError(f'Unknown label in getNode: {label}')


    def _collectInterHighs(self, types, ctx):
        self._collectInterHighs(types, ctx.lhs_) if ctxLabel(ctx.lhs_) == 'inter_high' else types.insert(0, self._getNode(ctx.lhs_))
        self._collectInterHighs(types, ctx.rhs_) if ctxLabel(ctx.rhs_) == 'inter_high'  else types.append(self._getNode(ctx.rhs_))
        return types

    def _collectInters(self, types, ctx):
        self._collectInters(types, ctx.lhs_) if ctxLabel(ctx.lhs_) in ('inter', 'inter_low') else types.insert(0, self._getNode(ctx.lhs_))
        self._collectInters(types, ctx.rhs_) if ctxLabel(ctx.rhs_) in ('inter', 'inter_low')  else types.append(self._getNode(ctx.rhs_))
        return types

    def _collectUnions(self, types, ctx):
        self._collectUnions(types, ctx.lhs_) if ctxLabel(ctx.lhs_) == 'union' else types.insert(0, self._getNode(ctx.lhs_))
        self._collectUnions(types, ctx.rhs_) if ctxLabel(ctx.rhs_) == 'union' else types.append(self._getNode(ctx.rhs_))
        return types

    def _collectTuples(self, types, ctx):
        self._collectTuples(types, ctx.lhs_) if ctxLabel(ctx.lhs_) == 'tuple' else types.insert(0, self._getNode(ctx.lhs_))
        self._collectTuples(types, ctx.rhs_) if ctxLabel(ctx.rhs_) == 'tuple' else types.append(self._getNode(ctx.rhs_))
        return types

    def _collectFields(self, fields, ctx):
        fields.append((ctx.name_.text, self._getNode(ctx.type_)))
        return self._collectFields(fields, ctx.rhs_) if getattr(ctx, 'rhs_', Missing) else fields

    def _checkExplicit(self, ctx, t):
        if not t.explicit:
            raise ValueError(f'{t} already defined as not being explicitly matched: {ctx.start.line}-{ctx.stop.line}')

    def _raiseUnknownVariableEncountered(self, recname, var, ctx):
        raise ValueError(f'Unassigned implicit recursive variable "{recname}" found whilst assigning "{var}": {ctx.start.line}-{ctx.stop.line}')

    def _raiseSecondImplicitRecursiveFound(self, var, ctx):
        raise ValueError(f'Another implicit recursive "{var}" found before current implicit recursive is assigned: {ctx.start.line}-{ctx.stop.line}')

    def _rootAtomContext(self, ctx):
        if ctxLabel(ctx) == 'atom_multi':
            return self._rootAtomContext(ctx.rhs_)
        else:
            return ctx

    def _assign_atom(self, varname, explicit, space, implicity, ctx):
        self.ast.append(
            Set(
                varname,
                Atom(explicit, space, implicity, varname, SrcLoc(ctx)),
                SrcLoc(ctx)
            )
        )
        self._nodeByCtx[ctx] = self.ast[-1]

