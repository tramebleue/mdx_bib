# Bibliography and Citation support for Python-Markdown

This extension to Python Markdown is inspired by the support for citations in [R Markdown][].
It looks for all citation keys with the form `@<citekey>` inside matching square brackets and appends a bibliography to the output.
The references associated with the citation keys can be defined manually or generated from a BibTeX file.

## Installation

Running 

```bash
$ python setup.py install
```

will install a module named `mdx_bib`.

```python
import markdown
from mdx_bib import CitationExtension

cite = CitationExtension(bibtex_file='/path/to/library.bib', order='unsorted')
html = markdown.markdown(text, extensions=[cite])
```

## Defining References

This extension will first look for any manually defined bibligraphy entries, for example

    [@barney04]: Barneby, C.D. *A review of reviews*. Annual Reviews of Something (2104)

If a matching reference definition cannot be found, then the extension looks in the BibTeX file for a matching citation key.

## Citing

Citation keys are any identifiers inside square brackets with a `@`-prefix

    Some claim [@adams98].
    Some claim [@adams98; @barney04].

will render, according to your bibliography database, to:

Some claim ([Adams, 1998][@adams98]).

Some claim ([Adams, 1998][@adams98]; [Barney, 2004][@barney04])

You can also insert citations in the running text,
by prefixing the citekey with some introduction text.
The `+` sign switches from the former format to the latter.

    Some claim, [see @adams98]. [+@barney04] also says ...

[R Markdown]: http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html
[@adams98]: #adams98
[@barney04]: #barney04

