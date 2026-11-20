import html
import os
import re
import xml.etree.ElementTree as ET

import httpx
from dotenv import load_dotenv

load_dotenv()

USER_AGENT = os.getenv("USER_AGENT")
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"
MAX_CHARS = 3000
ARXIV_STOPWORDS = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "is", "not", "of", "on", "or", "the", "to", "with"}
HEADING_RE = re.compile(r"^(=+) (.+?) =+$", re.M)


def wikipedia_search(q):
    results = httpx.get(WIKIPEDIA_API, params={
        "action": "query",
        "list": "search",
        "srsearch": q,
        "srlimit": 3,
        "format": "json"
    }, headers={"User-Agent": USER_AGENT}).raise_for_status().json()["query"]["search"]
    if not results:
        return f"No Wikipedia results for '{q}'"
    return "\n".join(f"{r['title']}: {strip_html(r['snippet'])}" for r in results)


def wikipedia_page(q):
    title, _, section = q.partition("#")
    page = next(iter(httpx.get(WIKIPEDIA_API, params={
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "redirects": 1,
        "titles": title.strip(),
        "format": "json"
    }, headers={"User-Agent": USER_AGENT}).raise_for_status().json()["query"]["pages"].values()))
    if "missing" in page:
        return f"No Wikipedia page called '{title.strip()}'. Try wikipedia_search first."
    text = page["extract"]
    headings = list(HEADING_RE.finditer(text))
    section_list = "Sections: " + ", ".join(h[2] for h in headings if len(h[1]) == 2)
    if not section:
        intro = text[:headings[0].start()] if headings else text
        return f"{intro.strip()[:MAX_CHARS]}\n\n{section_list}"
    index = next((i for i, h in enumerate(headings) if h[2].lower() == section.strip().lower()), None)
    if index is None:
        return f"No section '{section.strip()}' in {page['title']}. {section_list}"
    return section_text(text, headings, index)


def arxiv_search(q):
    response = httpx.get(ARXIV_API, params={
        "search_query": " AND ".join(f"all:{word}" for word in arxiv_words(q)),
        "max_results": 3,
    }, headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True).raise_for_status()
    entries = ET.fromstring(response.text).findall(f"{ATOM}entry")
    if not entries:
        return f"No arXiv results for '{q}'"
    return "\n\n".join(format_paper(entry) for entry in entries)


def calculate(what):
    return eval(what)


def section_text(text, headings, index):
    level = len(headings[index][1])
    inner = []
    end = len(text)
    for h in headings[index + 1:]:
        if len(h[1]) <= level:
            end = h.start()
            break
        if len(h[1]) == level + 1:
            inner.append(h[2])
    body = text[headings[index].end():end].strip()
    if len(body) <= MAX_CHARS:
        return body
    note = f"Ask for one of these subsections: {', '.join(inner)}" if inner else "The rest is cut off."
    return f"{body[:MAX_CHARS]}\n\n[Truncated. {note}]"


def arxiv_words(q):
    return [word for word in re.findall(r"\w+", q) if word.lower() not in ARXIV_STOPWORDS]


def format_paper(entry):
    title = " ".join(entry.findtext(f"{ATOM}title").split())
    authors = ", ".join(a.findtext(f"{ATOM}name") for a in entry.findall(f"{ATOM}author"))
    published = entry.findtext(f"{ATOM}published")[:10]
    summary = " ".join(entry.findtext(f"{ATOM}summary").split())
    return f"{title} ({published}, {entry.findtext(f'{ATOM}id')})\nAuthors: {authors}\n{summary[:800]}"


def strip_html(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text))


known_actions = {
    "wikipedia_search": wikipedia_search,
    "wikipedia_page": wikipedia_page,
    "arxiv_search": arxiv_search,
    "calculate": calculate,
}


if __name__ == "__main__":
    print(wikipedia_search("ReAct language model"))
    print(wikipedia_page("Large language model")[-300:])
    print(wikipedia_page("Large language model#History")[:300])
    print(wikipedia_page("Nowhereville Zzq"))
    print(arxiv_search("ReAct reasoning acting language models"))
    print(arxiv_search("zzqqxxnotapaperqqzz"))
