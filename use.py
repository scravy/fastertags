import sys

import fastertags as h

if __name__ == "__main__":
    h.document(
        title="Some nice document",
        body=[
            h.div(
                h.div(
                    class_="booya",
                    id="",
                    data_what_for="what else is there?",
                ).on(
                    "click",
                    "alert('<hello>');",
                )(
                    h.style(
                        """
                            span {
                                color: red;
                            }
                        """
                    ),
                    "Something",
                    h.span(
                        "hey ya",
                    ),
                ),
                h.label(
                    h.span(class_="boom")(
                        "Query",
                    ),
                    h.input(
                        type="text",
                    ),
                ),
                h.button("button").hx(
                    render=h.html(
                        h.head(h.title("such a new title")),
                        h.body(
                            h.h1(style="color: red")("Hello, World!"),
                        ),
                    ),
                    swap="innerHTML",
                )("more button"),
            ),
        ],
    ).print(oob_handler=lambda _fp, obj: print(obj, file=sys.stderr))
