import textwrap
import xml.etree.ElementTree as et
from typing import *


StrGen: TypeAlias = Generator[str, None, None]


class Parser:
    def __init__(self, tree: et.ElementTree) -> None:
        self.tree = tree
        self.numbered_seclvl: int = 0
        self.secnums: list[int] = list()
        self.seclvl: int = -1

    # --- DISPATCHERS --------------------------------------------------

    def dispatch_from_paragraph(self, el: et.Element) -> StrGen:
        match el.tag:
            case "Literal":
                yield from self.handle_inline_literal(el)
            case "Bold":
                yield from self.handle_inline_bold(el)
            case "Italic":
                yield from self.handle_inline_italic(el)
            case _:
                raise ValueError(f"Unknown tag within text content: {el.tag!r}")

    def dispatch_from_document(self, el: et.Element) -> StrGen:
        match el.tag:
            case "Section":
                yield from self._handle_section(el)
            case _:
                raise ValueError(f"Unknown tag within 'Document': {el.tag!r}")

    def dispatch_from_section(self, el: et.Element) -> StrGen:
        match el.tag:
            case "Paragraph":
                yield from self.handle_paragraph(el)
            case "BlockQuote":
                yield from self.handle_blockquote(el)
            case "Code":
                yield from self._handle_code(el)
            case _:
                raise ValueError(f"Unknown tag within 'Section': {el.tag!r}")

    def dispatch_from_blockquote(self, el: et.Element) -> StrGen:
        match el.tag:
            case "Paragraph":
                yield from self.handle_paragraph(el)
            case "Blockquote":
                yield from self.handle_blockquote(el)
            case _:
                raise ValueError(f"Unknown tag within 'BlockQuote': {el.tag!r}")


    # --- UTILITIES ----------------------------------------------------

    def lines(self, chunks: Iterable[str]) -> StrGen:
        for chunk in chunks:
            yield from chunk.split("\n")

    def dispatch_with_breaks(
        self, el: et.Element, dispatcher: Callable[[et.Element], StrGen]
    ) -> StrGen:
        max_idx = len(el)
        nobreak: bool = False
        for i, child in enumerate(el):
            if child.tag == "NoBreak":
                nobreak = True
                continue
            elif nobreak is True:
                nobreak = False
            elif i and i < max_idx:
                yield ""
            yield from dispatcher(child)

    def indented(self, lines: Iterable[str], indent: str) -> StrGen:
        for line in lines:
            if line:
                yield indent + line
            else:
                yield ""


    # --- BUILTIN HANDLERS ---------------------------------------------

    def handle_document(self, el: et.Element) -> StrGen:
        for child in el:
            yield from self.dispatch_from_document(child)

    def _handle_section(self, el: et.Element) -> StrGen:
        numbered = el.attrib.get("numbered", "").lower() == "true"

        if numbered:
            self.numbered_seclvl += 1
            if len(self.secnums) < self.numbered_seclvl:
                self.secnums.append(0)
            else:
                self.secnums = self.secnums[:self.numbered_seclvl]
            self.secnums[-1] += 1

        self.seclvl += 1

        yield from self.handle_section(
            el, el.attrib["title"], numbered
        )

        self.seclvl -= 1

        if numbered:
            self.numbered_seclvl -= 1

    def handle_paragraph(self, el: et.Element) -> StrGen:
        def gen() -> StrGen:
            if el.text:
                if len(el) > 0:
                    yield el.text.lstrip()
                else:
                    yield el.text.strip()

            last_idx = len(el) - 1
            for i, child in enumerate(el):
                yield from self.dispatch_from_paragraph(child)
                if child.tail:
                    if i == last_idx:
                        yield child.tail.rstrip()
                    else:
                        yield child.tail

        yield "".join(gen())

    def _handle_code(self, el: et.Element) -> StrGen:
        yield from self.handle_code(el, el.attrib.get("lang"))


    # --- USER-DEFINED HANDLERS ----------------------------------------

    def handle_section(
        self, el: et.Element, title: str, numbered: bool
    ) -> StrGen:
        title = title.strip()

        if numbered:
            nums = ".".join(map(str, self.secnums))
            title = f"{nums}  {title}"

        line_chars = (
            "=", "-", "`", ":", ".", "'", "\"", "~", "^", "_", "*", "+", "#",
            "!", "$", "%", "&", "(", ")", ",", "/", ":", ";", "<", ">", "?",
            "@", "[", "\\", "]", "{", "|", "}",
        )
        line = line_chars[self.seclvl] * (len(title) + 1)

        yield from (line, f" {title}", line)
        yield ""
        yield from self.dispatch_with_breaks(el, self.dispatch_from_section)

    def handle_inline_literal(self, el: et.Element) -> StrGen:
        yield f"``{el.text.strip()}``"

    def handle_inline_bold(self, el: et.Element) -> StrGen:
        yield f"**{el.text.strip()}**"

    def handle_inline_italic(self, el: et.Element) -> StrGen:
        yield f"*{el.text.strip()}*"

    def handle_blockquote(self, el: et.Element) -> StrGen:
        yield from self.dispatch_with_breaks(
            el,
            lambda e: self.indented(self.dispatch_from_blockquote(e), "    ")
        )

    def handle_code(self, el: et.Element, lang: str | None) -> StrGen:
        lines = textwrap.dedent(el.text).strip("\n").splitlines()

        if lang:
            yield f".. code-block:: {lang}"
        else:
            yield ".. code-block::"

        yield from self.indented(lines, "    ")


    # --- ENTRYPOINT ---------------------------------------------------

    def _parse(self) -> StrGen:
        root = self.tree.getroot()
        if root is None or root.tag != "Document":
            raise ValueError("The root element must be a `Document`")
        yield from self.handle_document(root)

    @classmethod
    def parse(cls, tree: et.ElementTree) -> str:
        parser = cls(tree)
        return "\n".join(parser._parse())




tree = et.parse("./docs/test.xml")
parser = Parser(tree)
with open("test.rst", "w") as outfile:
    for line in parser._parse():
        print(repr(line))
        outfile.write(f"{line}\n")

# print(tuple(p.itertext()))


# for child in p:
#     print(child)



