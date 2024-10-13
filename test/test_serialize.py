import fastertags as h


def test_serialize_simple() -> None:
    doc = h.html(
        h.head(
            h.title("TITLE"),
        ),
        h.body(
            h.h1("HEADING"),
            h.p("PARAGRAPH 1"),
            h.p("PARAGRAPH 2"),
        ),
    )
    assert str(doc) == (
        "<!DOCTYPE html><html><head><title>TITLE</title></head>"
        "<body><h1>HEADING</h1><p>PARAGRAPH 1</p><p>PARAGRAPH 2</p></body></html>"
    )


def test_serialize_style() -> None:
    doc = h.html(
        h.head(h.title("TITLE"), h.style("not { scoped }")),
        h.body(
            h.h1("HEADING"),
            h.div(
                h.style("scoped"),
                h.p("PARAGRAPH 1"),
                h.p("PARAGRAPH 2"),
            ),
        ),
    )
    assert str(doc) == (
        "<!DOCTYPE html><html><head><title>TITLE</title><style>not { scoped }</style></head>"
        "<body><h1>HEADING</h1><div><style>@scope {scoped}</style><p>PARAGRAPH 1</p><p>PARAGRAPH 2</p></div>"
        "</body></html>"
    )


def test_serialize_data() -> None:
    doc = h.div(data_custom="SOMETHING")("text content")
    assert str(doc) == ("""<div data-custom="SOMETHING">text content</div>""")


def test_serialize_escape() -> None:
    doc = h.div("text <content>")
    assert str(doc) == ("""<div>text &lt;content></div>""")


def test_serialize_no_escape() -> None:
    doc = h.div(data_custom="SOMETHING")("text content: ", h.NoEscape("<b>bold</b>"))
    assert str(doc) == (
        """<div data-custom="SOMETHING">text content: <b>bold</b></div>"""
    )


def test_repr() -> None:
    doc: h.HTMLElement

    doc = h.div().on("click", "alert('hello')")
    assert repr(doc) == r"""div().on('click', "alert('hello')")"""

    doc = h.div(class_="str")
    assert repr(doc) == "div(class_='str')"

    doc = h.del_()
    assert repr(doc) == "del_()"

    doc = h.p("text", "more text")
    assert repr(doc) == "p('text', 'more text')"

    doc = h.p(id="para")("text", "more text")
    assert repr(doc) == "p(id='para')('text', 'more text')"
