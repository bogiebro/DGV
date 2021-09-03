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
        make_edges(self.gdatalog, self.bindings, parse(code))

class GDatalog():
    def __init__(self):
        pass
    
    def bind(self, *code: tuple[str, ...]):
        return Binder(self, parse(code))

def make_edges(
        gdatalog: GDatalog,
        in_bindings: dict[Location, Binding],
        out_bindings: dict[Location, Binding]):
    scope = {}
    for k, v in in_bindings.items():
        if isinstance(v, LocalVar):
            scope[v] = k
    for k,v in out_bindings.items():
        if isinstance(v, LocalVar):
            if v in scope:
                print(scope[v], "->", k)
        elif isinstance(v, FuncApp):
            for arg in v[1:]:
                if isinstance(arg, LocalVar):
                    print(scope[arg], "->", v[0])
            print(v[0], "->", k)


g = GDatalog()
# g.bind("foo(x)").to("bar(x)")
g.bind("foo(x=z)").to("bar(x=foo(z))")
