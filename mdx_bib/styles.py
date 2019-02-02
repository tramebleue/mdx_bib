from pybtex.style.formatting.unsrt import Style, date, pages
from pybtex.richtext import Symbol, Text
from pybtex.style.formatting import toplevel
from pybtex.richtext import Text, Tag
from pybtex.style.template import (
    field, first_of, href, join, names, optional, optional_field, sentence,
    tag, together, words, _format_list
)
from pybtex.style.names import lastfirst

class APAStyle(Style):

    def __init__(self, name_style=lastfirst.NameStyle, abbreviate_names=True, *args, **kwargs):
        kwargs['name_style'] = name_style
        kwargs['abbreviate_names'] = abbreviate_names
        super().__init__(*args, **kwargs)

    def get_article_template(self, e):
        volume_and_pages = first_of [
            # volume and pages, with optional issue number
            optional [
                join [
                    field('volume'),
                    optional['(', field('number'),')'],
                    ':', pages
                ],
            ],
            # pages only
            words ['pages', pages],
        ]
        template = toplevel [
            self.format_names('author'),
            join ['(', field('year'), ').'],
            self.format_title(e, 'title'),
            sentence [
                tag('em') [field('journal')],
                optional[ volume_and_pages ]],
            sentence [ optional_field('note') ],
            self.format_web_refs(e),
        ]
        return template

