from twisted.internet.defer import inlineCallbacks, returnValue
from twilix.stanzas import Iq, Message, Presence, Stanza
from twilix.jid import internJID
from twilix.base import MyElement, WrongElement, EmptyStanza, ElementParseError, BreakStanza
from twilix import errors

class Dispatcher(object):
    def __init__(self, xs, myjid):
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
        if not handler in self._handlers:
            self._handlers.append(handler)
            return True

    def unregisterHandler(self, handler):
        if handler in self._handlers:
            self._handlers.remove(handler)
            return True

    @inlineCallbacks
    def dispatch(self, el):
        results = []
        el = MyElement.makeFromElement(el)
        for cls in (Iq, Message, Presence):
            try:
                el = cls.createFromElement(el, dont_defer=True)
            except WrongElement:
                pass

        if el.type_ in ('result', 'error') and self._callbacks.has_key(el.id):
            id = el.id
            deferred, result_class, error_class = self._callbacks[id]
            if result_class is not None and el.type_ == 'result':
                try:
                    el = result_class.createFromElement(el, None)
                except (WrongElement, ElementParseError), e:
                    deferred.errback(e)
                else:
                    deferred.callback(el)
            elif result_class is None and el.type_ == 'result':
                deferred.callback(el)
            elif el.type_ == 'error':
                exception = None
                try:
                    err = error_class.createFromElement(el, None)
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
                    d = handler.createFromElement(el, host, dont_defer=True)
                    d.validate()
                except WrongElement:
                    continue
                except ElementParseError:
                    bad_request = True
                    continue
                func = getattr(d, '%sHandler' % d.topElement().type_, None) or \
                       getattr(d, 'anyHandler', None)
                if func is not None:
                    result = yield func()
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
                self.send(el.makeError("cancel",
                                       "service-unavailable"))
            elif el.type_ not in ('error', 'result') and bad_request:
                self.send(el.makeError("modify",
                                       "bad-request"))
            elif el.type_ not in ('error', 'result') and isinstance(el, Iq):
                self.send(el.makeError("cancel",
                                       "feature-not-implemented"))
        returnValue(None)

    def send(self, els):
        deferred = None
        if not isinstance(els, (tuple, list)):
            deferred = getattr(els, 'deferred', None)
            els = (els,)
        for el in els:
            if isinstance(el, (EmptyStanza, BreakStanza)):
                continue
            hooks = self.getHooks('send')
            for hook, host in hooks:
                try:
                    d = hook.createFromElement(el, host)
                    d.validate()
                except WrongElement:
                    continue

                func = getattr(d, '%sHandler' % d.topElement().type_, None) or \
                       getattr(d, 'anyHandler', None)
                if func is None:
                    continue
                el = func()
                if isinstance(el, (EmptyStanza, BreakStanza)):
                    return
            if el.type_ in ('set', 'get') and el.deferred is not None:
                self._callbacks[el.id] = (el.deferred, el.result_class, el.error_class)
            self.xmlstream.send(el)
        return deferred
