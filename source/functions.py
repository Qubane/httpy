def parse_md2html(text: list[str]) -> list[str]:
    """
    Parses md to html
    :param text: md formatted string
    :return: html formatted string
    """

    # make formatting
    is_bold = False
    is_italics = False
    for _ in range(len(text)):
        line = text.pop(0)
        new_line = ""
        format_buffer = ""
        for char in line:
            if char == "*":
                format_buffer += char
                continue
            if format_buffer == "*" and char != "*":
                format_buffer = ""
                is_italics = not is_italics
                if is_italics:
                    new_line += "<i>"
                else:
                    new_line += "</i>"
            if format_buffer == "**" and char != "*":
                format_buffer = ""
                is_bold = not is_bold
                if is_italics:
                    new_line += "<b>"
                else:
                    new_line += "</b>"
            new_line += char
        text.append(new_line)

    # make headers
    for _ in range(len(text)):
        line = text.pop(0)
        if len(line) == 0:
            continue
        if line[0] == "#":
            header = 1
            if len(line) > 2 and line[1] == "#":
                header = 2
            if len(line) > 3 and line[2] == "#":
                header = 3
            text.append(f"<h{header}>{line[header:].strip()}</h{header}>")
            continue
        text.append(f"<p>{line.strip()}</p>")

    return text
