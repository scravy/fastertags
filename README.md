# fastertags, an HTML tag library

A typesafe library for writing HTML in Python:

```
import fastertags as h

if __name__ == "__main__":
    doc = h.html(
        h.head(
            h.title("An example document"),
        ),
        h.body(
            h.h1("Title"),
            h.p(class_="css-class-name")("some paragraph"),
            h.p("Some more paragraph"),
        ),
    )
    print(doc)
```

yields

```
<!DOCTYPE html><html><head><title>An example document</title></head><body><h1>Title</h1><p class="css-class-name">some paragraph</p><p>Some more paragraph</p></body></html>
```

Tags and Attributes are scraped from the WHATWG HTML Spec
at [https://html.spec.whatwg.org/](https://html.spec.whatwg.org/).  Version numbers reflect when the scraping was done,
the current version `0.2024.9` was taken in September 2024.

## HTMX

`fastertags` is a standalone building block for `fasterhtml`, which in turn uses HTMX.  Most notably, `fastertags`
serializes event-handler `on*` attributes as `hx-on:*`, for example `hx-on:click` instead of `onclick`.

This can be changed by setting `HTMLElement.EVENT_HANDLER_PREFIX`:

```
doc = h.h1().on("click", "alert('clicked')")("Title")

print(doc)
# <h1 hx-on:click="alert('clicked')">Title</h1>

h.HTMLElement.EVENT_HANDLER_PREFIX= "on"

print(doc)
# <h1 onclick="alert('clicked')">Title</h1>
```

## Scoped CSS

`fastertags` emulates the `scoped` attributes on `<style>` tags by wrapping its contents in `@scope { ... }`.
The `h.style()` function does feature the boolean attribute `scoped` that allows for `True`, `False`, or `None`.
The default is `None`, which means contents will be wrapped in `@scope { ... }` if the element is not serialized
as the child of a `head` element:

```
doc = h.html(
    h.head(
        h.style("not scoped"),
    ),
    h.body(
        h.style("scoped"),
    ),
)
print(doc)
```

yields

```
<!DOCTYPE html><html><head><style>not scoped</style></head><body><style>@scope {scoped}</style></body></html>
```
