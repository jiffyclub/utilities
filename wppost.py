#!/usr/bin/env python
"""
I write blog posts in Markdown in my favorite text editor, but when I go
to post to WordPress it treats newlines as hard wraps instead of the usual
HTML behavior of letting everything within a block wrap on its own.

This script modifies the markdown processor to remove newlines from paragraph
blocks so that they appears on a single line.

Markdown text is read from a specified file and the converted HTML is
sent to stdout.

"""

import argparse
import sys

import markdown
from markdown.util import etree


class WPParagraph(markdown.blockprocessors.ParagraphProcessor):
    def run(self, parent, blocks):
        """
        This will strip newlines from any block of text that's destined
        to go into a <p> tag. To get the changes into the final document
        we add a new element to the parent and fill it with the modified
        text.

        """
        block = blocks.pop(0).replace('\n', ' ')
        p = etree.SubElement(parent, 'p')
        p.text = block


class WPExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        """
        Replace the default paragraph processor with the modified one.
        Processors are instantiated with a BlockParser instance.

        """
        md.parser.blockprocessors['paragraph'] = WPParagraph(md.parser)


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description='Format a markdown document as HTML for posting on WordPress.')
    parser.add_argument('file', type=argparse.FileType('r'),
        help='Markdown file to parse.')
    return parser.parse_args(args)


def main(args=None):
    args = parse_args(args)
    md = args.file.read()
    html = markdown.markdown(md, extensions=['extra', 'smarty', WPExtension()],
        output_format='html5')
    print(html)


if __name__ == '__main__':
    sys.exit(main())
