"""
Realize elements of XHTML-IM protocol. Provides the ability to send 
messages with simple html markup.
"""
from twilix.base.velement import VElement
from twilix import fields

class HtmlHead(VElement):
    """
    Extends VElement class from twilix.base
    Realize head tag of html.
    """
    elementName = 'head'

    profile = fields.StringAttr('profile', required=False)
    title = fields.StringNode('title')

class HtmlBody(VElement):
    """
    Extends VElement class from twilix.base
    Realize body tag of html.
    """
    elementName = 'body'
    elementUri = 'http://www.w3.org/1999/xhtml'

class XHtmlIm(VElement):
    """
    Extends VElement class from twilix.base
    Realize element according xhtml-im protocol.
    """
    elementName = 'html'
    elementUri = 'http://jabber.org/protocol/xhtml-im'

    body = fields.ElementNode(HtmlBody)
    head = fields.ElementNode(HtmlHead, required=False)

