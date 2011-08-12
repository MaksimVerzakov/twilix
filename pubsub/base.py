from twilix import fields
from twilix.stanzas import Query, Message
from twilix.base import VElement

class CreateNodeElement(VElement):
    elementName = 'create'

    node = fields.StringAttr('node')

class Item(VElement):
    elementName = 'item'

    id_ = fields.StringAttr('id', required=False)
    publisher = fields.StringAttr('publisher', required=False)
    entry = fields.NodeProp(None, required=False)

class PublishElement(VElement):
    elementName = 'publish'

    node = fields.StringAttr('node')
    item = fields.ElementNode(Item)

class SubscribeElement(VElement):
    elementName = 'subscribe'

    node = fields.StringAttr('node')
    jid = fields.JidAttr('jid')

class UnsubscribeElement(SubscribeElement):
    elementName = 'unsubscribe'

    subid = fields.StringAttr('subid', required=False)

class Retract(VElement):
    elementName = 'retract'

    id_ = fields.StringAttr('id', required=True)

class Items(VElement):
    elementName = 'items'

    items = fields.ElementNode(Item, listed=True, required=False)
    node = fields.StringAttr('node')
    max_items = fields.StringAttr('max_items', required=False)
    retracts = fields.ElementNode(Retract, listed=True, required=False)

class Subscription(VElement):
    elementName = 'subscription'

    node = fields.StringAttr('node', required=False)
    jid = fields.JidAttr('jid')
    subscription = fields.JidAttr('subscription')
    subid = fields.StringAttr('subid', required=False)

class Subscriptions(VElement):
    elementName = 'subscriptions'

    node = fields.StringAttr('node', required=False)
    subscriptions = fields.ElementNode(Subscription, listed=True, required=False)

class Retract(VElement):
    elementName = 'retract'

    node = fields.StringAttr('node')
    items = fields.ElementNode(Item, listed=True)

class ConfigureNode(VElement):
    elementName = 'configure'

    node = fields.StringAttr('node')

class PubsubQuery(Query):
    elementName = 'pubsub'
    elementUri = 'http://jabber.org/protocol/pubsub'

    create_node = fields.ElementNode(CreateNodeElement, required=False)
    publish = fields.ElementNode(PublishElement, required=False)
    subscribe = fields.ElementNode(SubscribeElement, required=False)
    unsubscribe = fields.ElementNode(UnsubscribeElement, required=False)
    items = fields.ElementNode(Items, required=False)
    subscriptions = fields.ElementNode(Subscriptions, required=False)
    retract = fields.ElementNode(Retract, required=False)

class DeleteNodeElement(VElement):
    elementName = 'delete'

    node = fields.StringAttr('node')

class PubsubOwnerQuery(PubsubQuery):
    elementUri = 'http://jabber.org/protocol/pubsub#owner'

    delete_node = fields.ElementNode(DeleteNodeElement, required=False)
    configure_node = fields.ElementNode(ConfigureNode, required=False)

class Event(VElement):
    elementName = 'event'
    elementUri = 'http://jabber.org/protocol/pubsub#event'

    items = fields.ElementNode(Items, required=False)

class IncomingEvent(Message):
    event = fields.ElementNode(Event, required=False)

