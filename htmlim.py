from twilix.base import VElement
from twilix import fields

class HtmlHead(VElement):
    elementName = 'head'

    profile = fields.StringAttr('profile', required=False)
    title = fields.StringNode('title')

class HtmlBody(VElement):
    elementName = 'body'
    elementUri = 'http://www.w3.org/1999/xhtml'

class XHtmlIm(VElement):
    elementName = 'html'
    elementUri = 'http://jabber.org/protocol/xhtml-im'

    body = fields.ElementNode(HtmlBody)
    head = fields.ElementNode(HtmlHead, required=False)

