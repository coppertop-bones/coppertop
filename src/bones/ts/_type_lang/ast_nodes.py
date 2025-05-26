# **********************************************************************************************************************
# Copyright 2025 David Briant, https://github.com/coppertop-bones. Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the License. You may obtain a copy of the  License at
# http://www.apache.org/licenses/LICENSE-2.0. Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY  KIND,
# either express or implied. See the License for the specific language governing permissions and limitations under the
# License. See the NOTICE file distributed with this work for additional information regarding copyright ownership.
# **********************************************************************************************************************

from bones.core.sentinels import Missing
from bones.core.errors import ProgrammerError
from bones.ts.core import bmtnul


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


class TLNode:
    __slots__ = ['loc']
    def __init__(self, loc):
        self.loc = loc
    def eval(self, tm):
        children = self._evalChildren(tm)
        return self._evalSelf(tm, children)
    def _evalChildren(self, tm):
        return Missing
    def _evalSelf(self, tm, children, btype=Missing):
        raise NotImplementedError()
    def __repr__(self):
        return f'{self.__class__.__name__}<...>'


class GetNode(TLNode):
    __slots__ = ['name']
    def __init__(self, name, loc):
        super().__init__(loc)
        self.name = name
    def _evalSelf(self, tm, children, btype=Missing):
        if btype is not Missing: raise ProgrammerError()
        return tm.lookupOrImplicitTbc(self.name)
    def __repr__(self):
        return f'Get<"{self.name}">'


class BindNode(TLNode):
    __slots__ = ['name', 'expr_or_atom']

    def __init__(self, name, expr_or_atom, loc):
        super().__init__(loc)
        self.name = name
        self.expr_or_atom = expr_or_atom

    def _evalSelf(self, tm, children, btype=Missing):
        # We put the responsibility for confirming the details of deferred (including recursive) definitions here,
        # i.e. in the evaluation of the TL AST rather than in the TM.

        # we want something similar to Single Static Assignment but relaxed in the following ways:
        #  1) if name has been previously bound to a TBC then confirm its details
        #  2) if name has been previously bound to a type then check that we are just rebinding the same thing (throwing if now)
        #  3) if name has not been previously bound now bind it

        # sally: tbc          sally is id 65, bmttbc
        # sally: tbc - bad form tell the user they've tried to bind twice?
        # sally: atom         the bind must provide the id to atom node
        # joe: sally & fred       this should be checked post sbinding sally as the operation could be invalid if in same space?
        #                         or we allow it here but it will never be possible to do again
        # sally: f64 & rate   we have a problem   f64 & rate are id 67, sally is id 65, joe is 66
        #
        # to solve this the bind must provide the bytpeid to the interect so that f64 & rate has id 65
        #
        # we need the ability for a parent to instruct a node to eval it's children before deciding on the course of action to take
        # because bind includes confirming tbcs in the creation process
        # this makes the c code easier as the implicit recursion is handled in the Python TL execution rather than needing
        # putting that into the C typemanager

        if btype is not Missing: raise ProgrammerError()
        with tm.onErrRollback():
            grandChildren = self.expr_or_atom._evalChildren(tm)  # this may implicitly create and bind Tbcs
            if (current := tm.lookup(self.name)) and current.id:
                if tm.bmtid(current) == bmtnul:
                    child = self.expr_or_atom._evalSelf(tm, grandChildren, current)
                    tm.bind(self.name, child)
                else:
                    # rebinding wastes an id unless we add a way to discard this newly created child
                    child = self.expr_or_atom._evalSelf(tm, grandChildren)
                    tm.check(current, child)
                    child = current
            else:
                child = self.expr_or_atom._evalSelf(tm, grandChildren)
                tm.bind(self.name, child)
        return child

    def __repr__(self):
        return f'BindNode(\'{self.name}\')'


class AtomNode(TLNode):
    __slots__ = ['explicit', 'space', 'implicitly']
    def __init__(self, explicit, space, implicitly, loc):
        super().__init__(loc)
        self.explicit = explicit
        self.space = space
        self.implicitly = implicitly
    def _evalChildren(self, tm):
        return self.space.eval(tm) if self.space else Missing, self.implicitly.eval(tm) if self.implicitly else Missing
    def _evalSelf(self, tm, children, btype=Missing):
        space, implicitly = children
        return tm.initAtom(
            explicit=self.explicit,
            space=space,
            implicitly=implicitly,
            btype=btype
        )


class TbcNode(TLNode):
    __slots__ = ['main', 'space']
    def __init__(self, space, loc):
        super().__init__(loc)
        self.main = Missing
        self.space = space
    def _evalSelf(self, tm, children, btype=Missing):
        return tm.reserve(space=self.space.eval(tm) if self.space else Missing, btype=btype)


class MutableNode(TLNode):
    __slots__ = ['contained']
    def __init__(self, contained, loc):
        super().__init__(loc)
        self.contained = contained
    def _evalChildren(self, tm):
        return self.contained._evalChildren(tm)
    def _evalSelf(self, tm, children, btype=Missing):
        # OPEN: implement the bit that actions mutability
        return self.contained._evalSelf(tm, children, btype)


class InterNode(TLNode):
    __slots__ = ['types', 'space']
    def __init__(self, types, space, loc):
        super().__init__(loc)
        self.types = types
        self.space = space
    def _evalChildren(self, tm):
        return (
            tuple(sorted(
                (t.eval(tm) for t in self.types),
                key = lambda x:x.id
            )),
            self.space.eval(tm) if self.space else Missing
        )
    def _evalSelf(self, tm, children, btype=Missing):
        types, space = children
        return tm.intersection(types, space=space, btype=btype)
    def __repr__(self):
        return f'InterNode(... In ...)' if self.space else f'InterNode(...)'


class ExprNode(TLNode):
    __slots__ = ['op', 'argNodes']
    def __init__(self, op, argNodes, loc):
        super().__init__(loc)
        self.op = op
        self.argNodes = argNodes
    def _evalChildren(self, tm):
        return tuple(t[1].eval(tm) if isinstance(t, (list, tuple)) else t.eval(tm) for t in self.argNodes)
    def _evalSelf(self, tm, children, btype=Missing):
        if self.op == 'struct':
            names = tuple(an[0] for an in self.argNodes)
            return tm.struct(names, children, btype=btype)
        elif self.op == 'rec':
            names = tuple(an[0] for an in self.argNodes)
            return tm.rec(names, children, btype=btype)
        else:
            if self.op == 'union':
                return tm.union(tuple(sorted(children, key=lambda x:x.id)), btype=btype)
            elif self.op == 'tuple':
                return tm.tuple(children, btype=btype)
            elif self.op == 'seq':
                assert len(children) == 1
                return tm.seq(children[0], btype=btype)
            elif self.op == 'map':
                return tm.map(*children, btype=btype)
            elif self.op == 'fn':
                return tm.fn(*children, btype=btype)
            else:
                raise ValueError(f'Unknown op: {self.op}')
    def __repr__(self):
        return f'{self.op.capitalize()}(...)'


class CheckImplicitTbcsAreConfirmedNode(TLNode):
    __slots__ = []
    def __init__(self, loc):
        super().__init__(loc)
    def _evalSelf(self, tm, children, btype=Missing):
        return tm.checkImplicitRecursiveAssigned()
    def __repr__(self):
        return f'CheckImplicitTbcsAreConfirmedNode()'


class ReturnNode(TLNode):
    __slots__ = ['_expr']
    def __init__(self, expr, loc):
        super().__init__(loc)
        self._expr = expr
    def _evalSelf(self, tm, children, btype=Missing):
        answer = self._expr.eval(tm)
        tm.done()
        return answer
    def __repr__(self):
        return f'ReturnNode()'


class DoneNode(TLNode):
    __slots__ = []
    def __init__(self, loc):
        super().__init__(loc)
    def _evalSelf(self, tm, children, btype=Missing):
        return tm.done()
    def __repr__(self):
        return f'DoneNode()'

