import re
# import htmlmin


def minimize_html(html: bytes) -> bytes:
    """
    Minimizes HTML files.
    Slightly better than htmlmin for my files,
    but maybe I break something in process and I don't notice
    """

    html = bytearray(html)

    # remove newlines
    html = (html
            .replace(b'\r', b'')
            .replace(b'\n', b''))

    # remove double spaces
    size = len(html)
    while True:
        html = html.replace(b'  ', b'')

        # if nothing changes -> break
        if size == len(html):
            break
        size = len(html)

    # simplify '> <' to '><'
    html = html.replace(b'> <', b'><')

    # remove unnecessary quotes
    index = 0
    for tag in re.findall(r"<.*?>", html.decode("utf8")):
        index = html.find(tag.encode("utf8"), index)
        processed = (tag
                     .replace("\"", "")
                     .replace(": ", ":")
                     .replace("; ", ";"))
        if len(processed) < len(tag):
            html[index:index+len(tag)] = (html[index:index+len(tag)]
                                          .replace(tag.encode("utf8"), processed.encode("utf8"), 1))

    return html


def test():
    with open("../www/about.html", "rb") as file:
        original = file.read()

    processed = minimize_html(original)

    print(f"Original : {len(original)}\n"
          f"Processed: {len(processed)}\n"
          f"Rate     : {(1 - len(processed) / len(original)) * 100:.2f}%", end="\n\n")

    # processed = htmlmin.minify(original.decode("utf8"), True, True, True, True, True)
    #
    # print(f"Original : {len(original)}\n"
    #       f"Processed: {len(processed)}\n"
    #       f"Rate     : {(1 - len(processed) / len(original)) * 100:.2f}%")


if __name__ == '__main__':
    test()
