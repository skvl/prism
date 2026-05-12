import re
from dataclasses import dataclass, field
from typing import Any, Optional


TOKEN_RE = re.compile(
    r'(tag|type):(\S+)|'
    r'AND|OR|NOT|'
    r'"([^"]*)"|'
    r"(\S+)"
)


@dataclass
class QueryAST:
    terms: list[dict[str, Any]] = field(default_factory=list)


class QueryParser:
    def parse(self, query_str: str) -> QueryAST:
        ast = QueryAST()
        tokens = self._tokenize(query_str)
        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token.upper() in ("AND", "OR", "NOT"):
                ast.terms.append({"op": token.upper()})
                i += 1
                continue

            m = re.match(r'^(tag|type|path):(.+)$', token)
            if m:
                filter_type = m.group(1)
                filter_value = m.group(2)
                if filter_type == "path" and not filter_value.startswith("/"):
                    print(f"Warning: Paths must start with /. Treating '{token}' as text search.")
                    ast.terms.append({"text": token})
                else:
                    ast.terms.append({"filter": filter_type, "value": filter_value})
                i += 1
                continue

            ast.terms.append({"text": token})
            i += 1

        return ast

    def _tokenize(self, query_str: str) -> list[str]:
        tokens: list[str] = []
        i = 0
        while i < len(query_str):
            if query_str[i] in (" ", "\t"):
                i += 1
                continue
            if query_str[i] == '"':
                j = i + 1
                while j < len(query_str) and query_str[j] != '"':
                    j += 1
                tokens.append(query_str[i + 1:j])
                i = j + 1
                continue
            j = i
            while j < len(query_str) and query_str[j] not in (" ", "\t"):
                j += 1
            tokens.append(query_str[i:j])
            i = j
        return tokens
