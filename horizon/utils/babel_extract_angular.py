# Copyright 2015, Rackspace, US, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re

from six.moves import html_parser


# regex to find filter translation expressions
filter_regex = re.compile(
    r"""{\$\s*('([^']|\\')+'|"([^"]|\\")+")\s*\|\s*translate\s*\$}"""
)


class AngularGettextHTMLParser(html_parser.HTMLParser):
    """Parse HTML to find translate directives.

    Currently this parses for these forms of translation:

    <translate>content</translate>
        The content will be translated. Angular value templating will be
        recognised and transformed into gettext-familiar translation
        strings (i.e. "{$ expression $}" becomes "%(expression)")
    <p translate>content</p>
        The content will be translated. As above.
    {$ 'content' | translate $}
        The string will be translated, minus expression handling (i.e. just
        bare strings are allowed.)
    """

    def __init__(self):
        try:
            super(html_parser.HTMLParser, self).__init__()
        except TypeError:
            # handle HTMLParser not being a type in < Py3k
            html_parser.HTMLParser.__init__(self)

        self.in_translate = False
        self.inner_tags = []
        self.data = ''
        self.strings = []
        self.line = 0
        self.plural = False
        self.plural_form = ''
        self.comments = []

    def handle_starttag(self, tag, attrs):
        self.line = self.getpos()[0]
        if tag == 'translate' or \
                (attrs and 'translate' in [attr[0] for attr in attrs]):
                self.in_translate = True
                self.plural_form = ''
                for attr, value in attrs:
                    if attr == 'translate-plural':
                        self.plural = True
                        self.plural_form = value
                    if attr == 'translate-comment':
                        self.comments.append(value)
        elif self.in_translate:
            self.data += '<%s>' % tag
            self.inner_tags.append(tag)
        else:
            for attr in attrs:
                if not attr[1]:
                    continue
                for match in filter_regex.findall(attr[1]):
                    if match:
                        self.strings.append(
                            (self.line, u'gettext', match[0][1:-1], [])
                        )

    def handle_data(self, data):
        if self.in_translate:
            self.data += data
        else:
            for match in filter_regex.findall(data):
                self.strings.append(
                    (self.line, u'gettext', match[0][1:-1], [])
                )

    def handle_endtag(self, tag):
        if self.in_translate:
            if len(self.inner_tags) > 0:
                tag = self.inner_tags.pop()
                self.data += "</%s>" % tag
                return
            if self.plural_form:
                messages = (
                    self.data.strip(),
                    self.plural_form
                )
                func_name = u'ngettext'
            else:
                messages = self.data.strip()
                func_name = u'gettext'
            self.strings.append(
                (self.line, func_name, messages, self.comments)
            )
            self.in_translate = False
            self.data = ''
            self.comments = []


def extract_angular(fileobj, keywords, comment_tags, options):
    """Extract messages from angular template (HTML) files that use the
    angular-gettext translate directive as per
    https://angular-gettext.rocketeer.be/ .

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: This is a standard parameter so it isaccepted but ignored.

    :param comment_tags: This is a standard parameter so it is accepted but
                        ignored.
    :param options: Another standard parameter that is accepted but ignored.
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """

    parser = AngularGettextHTMLParser()

    for line in fileobj:
        parser.feed(line)

    for string in parser.strings:
        yield(string)
