class _CharIter:
    def __init__(self, string: str):
        self.string: str = string
        self._count: int = -1

    def next(self) -> str | None:
        self._count += 1
        return self.string[self._count] if self._count < len(self.string) else None

    def prev(self) -> str | None:
        self._count -= 1
        return self.string[self._count] if self._count > -1 else None

    def is_done(self):
        if self._count+1 >= len(self.string):
            return True
        return False

    @property
    def count(self) -> int:
        return self._count


def parse_md2html(text: str) -> str:
    """
    Parses md to html
    :param text: md formatted string
    :return: html formatted string list
    """

    out = ""
    text = text.replace("\r", "").replace("  \n", "\n")

    is_bold = False
    is_italics = False

    header = 0

    iterator = _CharIter(text)
    while not iterator.is_done():
        char = iterator.next()
        if char == "*":  # bold / italics
            if iterator.next() == "*":  # bold
                is_bold = not is_bold
                if is_bold:
                    out += "<b>"
                else:
                    out += "</b>"
            else:  # italics
                iterator.prev()
                is_italics = not is_italics
                if is_italics:
                    out += "<i>"
                else:
                    out += "</i>"
            continue
        if char == "\n":
            if header > 0:
                out += f"</h{header}>"
                header = 0
            else:
                out += "<br>"
            continue
        if char == "#":
            header = 1
            while (char := iterator.next()) == "#":
                header += 1
            if char != " ":  # not '# Text', but `#Text` thing
                iterator.prev()
            out += f"<h{header}>"
            is_header = True
            continue

        out += char

    return out
