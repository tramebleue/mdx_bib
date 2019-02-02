from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor
from markdown.postprocessors import Postprocessor
from markdown.inlinepatterns import Pattern
from markdown.util import etree

from pybtex.database.input import bibtex
from pybtex.style.template import FieldIsMissing

from collections import OrderedDict
import re

from .styles import APAStyle

BRACKET_RE = re.compile(r'\[([^\[]+)\]')
CITE_RE    = re.compile(r'@(\w+)')
DEF_RE     = re.compile(r'\A {0,3}\[@(\w+)\]:\s*(.*)')
INDENT_RE  = re.compile(r'\A\t| {4}(.*)')

CITATION_RE = r'\[([^@^\[]*)(@[a-zA-Z0-9;@\s]+)\]'
INNER_CITATION_RE = re.compile(r'@(\w+)')         

class Bibliography(object):
    """ Keep track of document references and citations for exporting """ 

    def __init__(self, extension, bibtex_file, order):
        self.extension = extension
        self.order = order
        
        self.citations = OrderedDict()
        self.references = dict()
        self.style = APAStyle()

        if bibtex_file:
            try:
                parser = bibtex.Parser()
                self.bibsource = parser.parse_file(bibtex_file).entries
            except:
                print("Error loading bibtex file")
                self.bibsource = dict()
        else:
            self.bibsource = dict()

    def addCitation(self, citekey):
        self.citations[citekey] = self.citations.get(citekey, 0) + 1

    def setReference(self, citekey, reference):
        self.references[citekey] = reference

    def citationID(self, citekey):
        return "cite-" + citekey

    def referenceID(self, citekey):
        return "ref-" + citekey

    def formatAuthor(self, author):
        out = "%s %s."%(author.last()[0], author.first()[0][0])
        if author.middle():
            out += "%s."%(author.middle()[0][0])
        return out

    def formatReference(self, key, entry):
        try:
            return self.style.format_entry(key, entry, self.bibsource).text.render_as('html')
        except FieldIsMissing as error:
            return self.formatError(key, error)

    def formatError(self, key, error):
        return '%s: <span style="color: red; font-weight: bold">%s</span>' % (key, error)

    def makeBibliography(self, root):
        if self.order == 'alphabetical':
            raise(NotImplementedError)

        div = etree.Element("div")
        div.set("class", "references")

        if not self.citations:
            return div

        for id in sorted(self.citations):

            ref_txt = etree.SubElement(div, "div")
            ref_txt.set("id", self.referenceID(id))
            ref_txt.set("class", "bibentry")
            if id in self.references:
                self.extension.parser.parseChunk(ref_txt, self.references[id])
            elif id in self.bibsource:
                par = etree.SubElement(ref_txt, "p")
                par.text = self.formatReference(id, self.bibsource[id])
            else:
                par = etree.SubElement(ref_txt, "p")
                par.text = self.formatError(id, 'Missing Citation')

        return div

class CitationsPreprocessor(Preprocessor):
    """ Gather reference definitions and citation keys """
    
    def __init__(self, bibliography):
        self.bib = bibliography

    def subsequentIndents(self, lines, i):
        """ Concatenate consecutive indented lines """
        linesOut = []
        while i < len(lines):
            m = INDENT_RE.match(lines[i])
            if m:
                linesOut.append(m.group(1))
                i += 1
            else:
                break
        return " ".join(linesOut), i

    def run(self, lines):
        linesOut = []
        i = 0

        while i < len(lines):
            # Check to see if the line starts a reference definition
            m = DEF_RE.match(lines[i])
            if m:
                key = m.group(1)
                reference = m.group(2)
                indents, i = self.subsequentIndents(lines, i+1)
                reference += ' ' + indents

                self.bib.setReference(key, reference)
                continue

            # Look for all @citekey patterns inside hard brackets
            for bracket in BRACKET_RE.findall(lines[i]):
                for c in CITE_RE.findall(bracket):
                    self.bib.addCitation(c)
            linesOut.append(lines[i])
            i += 1

        return linesOut
    
class CitationsPattern(Pattern):
    """ Handles converting citations keys into links """

    def __init__(self, pattern, bibliography):
        super(CitationsPattern, self).__init__(pattern)
        self.bib = bibliography

    def handleMatch(self, m):
        
        intro = m.group(2)
        citations = m.group(3)

        if intro:
            if len(intro) == 1:
                intro = ''
            template_et_al = '%s et al. (%s)'
            template = '%s (%s)'
            prefix = ''
            suffix = ''
        else:
            template_et_al = '%s et al., %s'
            template = '%s, %s'
            prefix = '('
            suffix = ')'

        container = etree.Element('span')
        container.text = intro
        citations = [m.group(1) for m in INNER_CITATION_RE.finditer(citations)]

        for i, citation in enumerate(citations):

            if citation in self.bib.citations:

                a = etree.SubElement(container, "a")
                a.set('id', self.bib.citationID(citation))
                a.set('href', '#' + self.bib.referenceID(citation))
                a.set('class', 'citation')

                if citation in self.bib.bibsource:

                    ref = self.bib.bibsource[citation]
                    authors = ref.persons['author']
                    year = ref.fields.get('year', '?')
                    if len(authors) > 1:
                        a.text = prefix + template_et_al % (authors[0].last()[0], year)
                    elif authors:
                        a.text = prefix + template % (authors[0].last()[0], year)
                    else:
                        a.text = prefix + citation
                else:
                    
                    a.text = prefix + citation

                if i < len(citations)-1:
                    a.tail = '; '
                    prefix = ''
                else:
                    a.text += suffix

        return container
    
class CitationsTreeprocessor(Treeprocessor):
    """ Add a bibliography/reference section to the end of the document """

    def __init__(self, bibliography):
        self.bib = bibliography
        
    def run(self, root):
        citations = self.bib.makeBibliography(root)
        root.append(citations)
    
class CitationsExtension(Extension):

    def __init__(self, *args, **kwargs):

        self.config = {
            "bibtex_file": ["",
                            "Bibtex file path"],
            'order': [
                "unsorted",
                "Order of the references (unsorted, alphabetical)"]
        }
        super(CitationsExtension, self).__init__(*args, **kwargs)
        self.bib = Bibliography(
            self,
            self.getConfig('bibtex_file'),
            self.getConfig('order'),
        )
                        
    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        self.parser = md.parser
        self.md = md

        md.preprocessors.add("mdx_bib",  CitationsPreprocessor(self.bib), "<reference")
        md.inlinePatterns.add("mdx_bib", CitationsPattern(CITATION_RE, self.bib), "<reference")
        md.treeprocessors.add("mdx_bib", CitationsTreeprocessor(self.bib), "_begin")

def makeExtension(*args, **kwargs):
    return CitationsExtension(*args, **kwargs)
