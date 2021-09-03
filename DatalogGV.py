from dataclasses import dataclass
from typing import Union
import ast
from functools import reduce
from itertools import chain
import inspect
from operator import or_

ClassName = str
VarName = str
Location = tuple[ClassName, VarName]
LocalVar = VarName
FuncApp = tuple
Constant = Union[int, bool]
Binding = Union[LocalVar, Constant, FuncApp]

def parse_call(arg: ast.Call) -> dict[Location, Binding]:
    result = {(arg.func.id, name.id): name.id for name in arg.args}
    for kw in arg.keywords:
        loc = (arg.func.id, kw.arg)
        if isinstance(kw.value, ast.Constant):
            result[loc] = kw.value.value
        elif isinstance(kw.value, ast.Name):
            result[loc] = kw.value.id
        elif isinstance(kw.value, ast.Call):
            result[loc] = tuple([
                kw.value.func.id, *[n.id for n in kw.value.args]])
    return result

def parse(code: tuple[str, ...]) -> dict[Location, Binding]:
    return reduce(or_, (parse_call(ast.parse(stmt).body[0].value) for stmt in code))

class Binder():
    def __init__(self, gdatalog, bindings: dict[Location, Union[Constant, LocalVar]]):
        self.gdatalog = gdatalog
        self.bindings = bindings

    def to(self, *code: list[str]):
        fg = make_edges(self.bindings, parse(code))
        connect(self.gdatalog, fg)

class GDatalog():
    def __init__(self):
        self.fg = []
    def bind(self, *code: tuple[str, ...]):
        return Binder(self, parse(code))

FuncNode = str
Node = Union[Location, FuncNode]
Edge = tuple[Node, Node]

@dataclass
class Gate:
    conditions: list[tuple[Location, Constant]]
    edges: 'FactorGraph'

FactorGraph = list[Union[Gate, Edge]]

def connect(g: GDatalog, fg: FactorGraph):
    g.fg.extend(fg) # note: not technically correct

def make_edges(
        in_bindings: dict[Location, Binding],
        out_bindings: dict[Location, Binding]) -> FactorGraph:
    scope = {}
    conditions = []
    for k, v in in_bindings.items():
        if isinstance(v, LocalVar):
            scope[v] = k
        else:
            conditions.append((k, v))
    edges = []
    for k,v in out_bindings.items():
        if isinstance(v, LocalVar):
            if v in scope:
                edges.append((scope[v], k))
        elif isinstance(v, FuncApp):
            for arg in v[1:]:
                if isinstance(arg, LocalVar):
                    edges.append((scope[arg], v[0]))
            edges.append((v[0], k))
    return [Gate(conditions, edges)] if conditions else edges


g = GDatalog()
g.bind("foo(x=z, y=True)", "bing(w)").to("bar(w, x=f(z))")
print(g.fg)
