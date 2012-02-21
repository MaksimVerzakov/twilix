"""
Module describes the Dispatcher : class which controlling any data exchange.
This class realize direct handling of input and output stanzas.

Dispatcher tries to determine if incoming stanza corresponding to the one of
registered handlers. If stanza was parsed successfully, dispatcher will try
to handle it with appropriate handler (based on stanza type) or send error
back if stanza was corrupted or handler for was not found. You may also use
an anyHandler which used for any stanza type.
"""

from twisted.internet.defer import inlineCallbacks, returnValue
from twilix.stanzas import Iq, Message, Presence, Stanza
from twilix.jid import internJID
from twilix.base.myelement import MyElement, EmptyStanza, BreakStanza
from twilix.base.exceptions import WrongElement, ElementParseError
from twilix.errors import ExceptionWithContent, InternalServerErrorException
from twilix import errors

class Dispatcher(object):
    """
    Main class for input-output controlling.
    
    Attributes :
    
        xs -- xmlstream
    
        myjid -- jabber id value
    
        _handlers -- list of (handler class, host)-style pairs 
                (see register/unregisterHandler methods)
    
        _callbacks -- dict of callbacks with format :
    
            key is an id of stanza that wait callback value
        
            value is a (deffered, resultclass, errorclass)-style tuple
    
    Methods :
        
        registerHandler -- adds new handler
        
        unregisterHandler -- dels some handler
        
        dispatch -- inlineCallbacks decorated method for handling of
        input stanzas
        
        send -- method realize sending of any stanzas
    
    """
    def __init__(self, xs, myjid):
        """Initializating by values of xmlstream and JID: listen to stanzas of
        any type and hadle it with the dispatch method, set a value to the
        myjid attribute."""
        self.xmlstream = xs
        self.xmlstream.addObserver('/message', self.dispatch)
        self.xmlstream.addObserver('/presence', self.dispatch)
        self.xmlstream.addObserver('/iq', self.dispatch)
        self._handlers = []
        self._hooks = {}
        self._callbacks = {}
        self.myjid = myjid

    def registerHook(self, hook_name, hook):
        hooks = self._hooks.get(hook_name, [])
        if not hook in hooks:
            hooks.append(hook)
            self._hooks[hook_name] = hooks
            return True

    def unregisterHook(self, hook_name, hook):
        hooks = self._hooks.get(hook_name, [])
        if hook in hooks:
            hooks.remove(hook)
            return True

    def getHooks(self, hook_name):
        return self._hooks.get(hook_name, ())

    def registerHandler(self, handler):
        """Registers new pair of any stanza handler class and it's host"""
        if not handler in self._handlers:
            self._handlers.append(handler)
            return True

    def unregisterHandler(self, handler):
        """Unregisters pair of any stanza handler class and it's host"""
        if handler in self._handlers:
            self._handlers.remove(handler)
            return True

    @inlineCallbacks
    def dispatch(self, el):
        """
        This function realize incoming data handling.
        
        There is a handling :
        
        -- returns callback/errorback value for result/error-type stanzas
        
        -- calls handlers for other stanzas and then send the results
        
        :param el: is an input stanza
        
        """
        results = []
        el = MyElement.makeFromElement(el)
        for cls in (Iq, Message, Presence):
            try:
                el = cls.createFromElement(el, dont_defer=True)
            except WrongElement:
                pass

        if el.type_ in ('result', 'error') and self._callbacks.has_key(el.id):
            # XXX: check sender here
            id = el.id
            deferred, result_class, error_class = self._callbacks[id]
            if result_class is not None and el.type_ == 'result':
                try:
                    el = result_class.createFromElement(el, host=None)
                # XXX: catch any exception here
                except (WrongElement, ElementParseError), e:
                    deferred.errback(e)
                else:
                    deferred.callback(el)
            elif result_class is None and el.type_ == 'result':
                deferred.callback(el)
            elif el.type_ == 'error':
                exception = None
                try:
                    err = error_class.createFromElement(el, host=None,
                                                        dispatcher=self)
                except (WrongElement, ElementParseError), e:
                    exception = e
                if exception is None:
                    exception = errors.exception_by_condition(err.error.condition)
                deferred.errback(exception)
            del self._callbacks[id]
        else:
            bad_request = False
            for handler, host in self._handlers:
                try:
                    d = handler.createFromElement(el, host=host,
                                                  dont_defer=True,
                                                  dispatcher=self)
                    d.topElement().validate()
                except WrongElement:
                    continue
                except ElementParseError, e:
                    bad_request = True
                    # TODO: pass an exception message?
                    continue
                func = getattr(d, '%sHandler' % d.topElement().type_, None) or \
                       getattr(d, 'anyHandler', None)
                if func is not None:
                    try:
                        result = yield func()
                    except Exception, e:
                        if not isinstance(e, ExceptionWithContent):
                            e = InternalServerErrorException()
                            raise
                            # TODO: Add traceback if debug
                        results.append(el.makeError(e.content))
                        break
                    else:
                        if isinstance(result, (list, tuple)):
                            results.extend(result)
                        elif result is not None:
                            results.append(result)
                        if (result and handler.topClass().elementName == 'iq') \
                          or filter(lambda x: isinstance(x, BreakStanza), results):
                            break       
            if results:
                self.send(results)
            elif el.to != self.myjid and el.type_ not in ('error', 'result'):
                self.send(el.makeError(errors.Error(condition="service-unavailable",
                                                    type_="cancel")))                        
            elif el.type_ not in ('error', 'result') and bad_request:
                self.send(el.makeError(errors.Error(type_="modify",
                                       condition="bad-request")))
            elif el.type_ not in ('error', 'result') and isinstance(el, Iq):
                self.send(el.makeError(errors.Error(type_="cancel",
                                       condition="feature-not-implemented")))
        returnValue(None)

    def send(self, els):
        """
        This function realize outgoing data handling.
        
        There is a handling :
        
        -- set callbacks for deferred stanza's objects
        
        -- send result stanzas
        
        :param els: is an output stanza or stanzas
        
        """
        deferred = None
        if not isinstance(els, (tuple, list)):
            els = (els,)
        for el in els:
            if isinstance(el, (EmptyStanza, BreakStanza)):
                continue
            top_el = el.topElement()
            #top_el.validate()
            hooks = self.getHooks('send')
            for hook, host in hooks:
                try:
                    d = hook.createFromElement(el, host=host)
                    d.topElement().validate()
                except WrongElement:
                    continue

                func = getattr(d, '%sHandler' % d.topElement().type_, None) or \
                       getattr(d, 'anyHandler', None)
                if func is None:
                    continue
                el = func()
                if isinstance(el, (EmptyStanza, BreakStanza)):
                    return
            if top_el.type_ in ('set', 'get') and top_el.deferred is not None:
                deferred = top_el.deferred
                result_class = top_el.result_class
                error_class = top_el.error_class
                assert result_class != 'self'
                assert error_class != 'self'
                self._callbacks[top_el.id] = (deferred, result_class, error_class)
            self.xmlstream.send(top_el)
        return deferred
