import contextlib
import dataclasses
import datetime
import hashlib
import json
import os.path
import pickle
import posixpath
import re
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

import urllib3
from bs4 import BeautifulSoup, Tag

_SCRIPT_DIR: Final[Path] = Path(__file__).parent


@contextlib.contextmanager
def timed(label: str):
    t0 = time.monotonic()
    yield
    d = time.monotonic() - t0
    print(d, "seconds", f"[{label}]")


def load_spec(url: str) -> str:
    hs = hashlib.sha256(url.encode("utf8")).hexdigest()[0:12]
    fn = _SCRIPT_DIR / f".{hs}.html"
    if not os.path.exists(fn):
        with open(fn, "wb") as fp:
            with timed("download"):
                resp = urllib3.request("GET", url)
                assert resp.status == 200
                fp.write(resp.data)
    with open(fn, "r", encoding="utf8") as fp:
        spec = fp.read()

    return spec


@dataclasses.dataclass
class Soup:
    base: str
    soup: BeautifulSoup


# noinspection PyDefaultArgument
def load_soup(url: str, cache: dict[str, Soup] | None = {}) -> Soup:
    urlc = urlparse(url)
    base = f"{urlc.scheme}://{urlc.netloc}{'/'.join(urlc.path.split('/')[0:-1])}"
    if cache is not None and url in cache:
        return cache[url]
    hs = hashlib.sha256(url.encode("utf8")).hexdigest()[0:12]
    fn = _SCRIPT_DIR / f".{hs}.pickle"
    if os.path.exists(fn):
        with timed(f"pickle.load: {url}"):
            with open(fn, "rb") as fp:
                soup = pickle.load(fp)
    else:
        spec = load_spec(url)
        with timed("parse"):
            soup = BeautifulSoup(spec, features="html5lib")
        with timed("pickle.dump"):
            with open(fn, "wb") as fp:
                pickle.dump(soup, fp)
    result = Soup(base, soup)
    if cache is not None:
        cache[url] = result
    return result


_ELEM_HREF: Final[re.Pattern] = re.compile(r"#the-\S+elements?")


def elements_from_toc(soup: Soup) -> Iterator[str]:
    elems = soup.soup.find(attrs={"id": "toc-semantics"}).css.select("li a")

    for elem in elems:
        if _ELEM_HREF.match(elem["href"]):
            for code in elem.css.select("code"):
                yield code.string


_MATCH_HEAD: Final[re.Pattern] = re.compile(r"^h[1-6]$")


def css_escape(s: str) -> str:
    return re.sub(r"([^a-zA-Z0-9_-])", r"\\\g<1>", s)


@dataclasses.dataclass
class Element:
    empty: bool = False
    attributes: dict[str, str] = dataclasses.field(default_factory=dict)


def scrape_elements(soup: Soup, elements: dict[str, Element]):
    elems = soup.soup.css.select("dfn[data-dfn-type='element']")
    elem: Tag
    sections: dict[str, set[str]] = dict()
    for elem in elems:
        parent = elem.parent
        if parent is None or not _MATCH_HEAD.match(parent.name):
            continue
        tags: set[str] = {
            tag.string for tag in elem.css.select("code") if tag.string not in elements
        }
        if not tags:
            continue
        section_id = elem.parent.attrs.get("id")
        if tags == {"marquee"}:
            continue
        if section_id in sections:
            sections[section_id].update(tags)
        else:
            sections[section_id] = tags
        if not section_id:
            print("WARNING", "no section id for", tags)
            continue

    for section_id, tags in sections.items():
        element = Element()
        try:
            definition = next(
                iter(soup.soup.css.select(f"#{css_escape(section_id)} ~ dl.element"))
            )
        except StopIteration:
            print("WARNING", "no definition for", tags, "@", section_id)
            continue

        attrlinks: dict[str, str] = {}

        current: str | None = None
        for child in definition.css.select("dt a, dd"):
            match child.name:
                case "a":
                    if child["href"].endswith("#concept-element-content-model"):
                        current = "content-model"
                    elif child["href"].endswith("#concept-element-attributes"):
                        current = "attributes"
                    else:
                        current = None
                case "dd":
                    match current:
                        case "content-model":
                            for a in child.css.select("a"):
                                if a["href"].endswith("#concept-content-nothing"):
                                    element.empty = True
                        case "attributes":
                            for a in child.css.select("a"):
                                if (
                                    a.parent.name == "code"
                                    and (
                                        "#attr" in a["href"]
                                        or a["href"].endswith("#ping")
                                    )
                                    and a.string not in attrlinks
                                ):
                                    attrlinks[a.string] = a["href"]

            for attr, link in attrlinks.items():
                element.attributes[attr] = process_attribute(soup, attr, link)

            for tag in tags:
                elements[tag] = element


def scrape_global_attributes(soup: Soup) -> Iterator[tuple[str, str]]:
    attributes: dict[str, str] = dict()
    for ix, ul in enumerate(soup.soup.css.select("#global-attributes ~ ul.brief")):
        if ix >= 2:
            break
        for el in ul.css.select("li code"):
            if el["id"].startswith("global-attributes:"):
                for a in el.css.select("a"):
                    attributes[a.string] = a["href"]

    for attr, link in attributes.items():
        yield attr, process_attribute(soup, attr, link)


def process_attribute(soup: Soup, name: str, link: str) -> str:
    type_ = "str"
    url, id_ = link.split("#")
    if url:
        url = posixpath.join(soup.base, url)
        soup = load_soup(url)
    for el in soup.soup.select("a[href$='#boolean-attribute']"):
        if (
            f"the-{name}-attribute" in el["id"]
            or len(el.parent.css.select(f"dfn#{css_escape(id_)}")) > 0
        ):
            type_ = "bool"
    return type_


def main():
    soup = load_soup("https://html.spec.whatwg.org/multipage/dom.html")

    global_attributes: dict[str, str] = {
        name: type_ for name, type_ in scrape_global_attributes(soup)
    }

    soup = load_soup("https://html.spec.whatwg.org/multipage/")
    docs = set()
    for el in soup.soup.css.select("#toc-semantics a"):
        doc = el["href"].split("#", maxsplit=1)[0]
        docs.add(doc)

    elements: dict[str, Element] = {
        "*": Element(attributes=global_attributes),
    }
    for doc in docs:
        docsoup = load_soup(f"https://html.spec.whatwg.org/multipage/{doc}")
        scrape_elements(docsoup, elements)

    with open(
        _SCRIPT_DIR / f"elements.{datetime.date.today().isoformat()}.json",
        "w",
        encoding="utf8",
    ) as fp:
        json.dump(elements, fp, indent=2, default=lambda obj: obj.__dict__)


if __name__ == "__main__":
    main()
