"""Unit test for threepy5.py (model layer)."""

import threepy5.threepy5 as py5
import threepy5.utils as utils
import unittest
from wx.lib.pubsub import pub
from collections import defaultdict


class listener(object):
    def __init__(self, topics=[]):
        self.calls = {}
        for t in topics:
            pub.subscribe(self.callback, t)
        
    def callback(self, topic=pub.AUTO_TOPIC, **kwargs):
        name = topic.getName()
        if not name in self.calls.keys():
            self.calls[name] = 0
        self.calls[name] += 1

    def addTopic(self, topic):
        pub.subscribe(self.callback, topic)


class DefaultValues(unittest.TestCase):
    def testCardDefaultValues(self):
        """Card should assign the correct default values for all properties."""
        card = py5.Card()
        self.assertEqual(card.rect, py5.NO_RECT)

    def testContentDefaultValues(self):
        """Content should assign the correct default values for all properties."""
        cont = py5.Content()
        self.assertEqual(cont.rect, py5.Content.DEFAULT_RECT)
        self.assertEqual(cont.kind, py5.DEFAULT_KIND)
        self.assertEqual(cont.rating,    py5.DEFAULT_RATING)
        self.assertEqual(cont.collapsed, False)
        self.assertEqual(cont.title,   "")
        self.assertEqual(cont.content, "")

    def testHeaderDefaultValues(self):
        """Header should assign the correct default values for all properties."""
        head = py5.Header()
        self.assertEqual(head.rect, py5.NO_RECT)
        self.assertEqual(head.header, "")

    def testImageDefaultValues(self):
        """Image should assign the correct default values for all properties."""
        img = py5.Image()
        self.assertEqual(img.rect, py5.NO_RECT)
        self.assertEqual(img.scale, py5.DEFAULT_SCALE)
        self.assertEqual(img.path, "")

    def testLineDefaultValues(self):
        """Line should assign the correct default values for all properties."""
        line = py5.Line()
        self.assertEqual(line.colour, py5.DEFAULT_COLOUR)
        self.assertEqual(line.thickness, py5.DEFAULT_THICKNESS)
        self.assertEqual(line.pts, [])

    def testAnnotationDefaultValues(self):
        """Annotation should assign the correct default values for all properties."""
        anno = py5.Annotation()
        self.assertEqual(anno.lines, [])

    def testCardGroupDefaultValues(self):
        """CardGroup should assign the correct default values for all properties."""
        grp = py5.CardGroup()
        self.assertEqual(grp.members, [])

    def testDeckDefaultValues(self):
        """Deck should assign the correct default values for all properties."""
        deck = py5.Deck()
        self.assertEqual(deck.name, "")
        self.assertEqual(deck.cards, [])
        self.assertEqual(deck.groups, [])

    def testAnnotatedDeckDefaultValues(self):
        """AnnotatedDeck should assign the correct default values for all properties."""
        annodk = py5.AnnotatedDeck()
        self.assertEqual(annodk.name, "")
        self.assertEqual(annodk.cards, [])
        self.assertEqual(annodk.groups, [])
        self.assertEqual(annodk.annotation.__class__, py5.Annotation)
        self.assertEqual(annodk.annotation.lines, [])

    def testBoxDefaultValues(self):
        """Box should assign the correct default values for all properties."""
        box = py5.Box()
        self.assertEqual(box.name, "")
        self.assertEqual(box.path, "")
        self.assertEqual(box.decks, [])



class InitValues(unittest.TestCase):
    test_id = 3
    test_rect = (1,2,3,4)
    test_members = [-1, 3, 10001]
    test_pts = [(1,2), (3,4), (-1,-1), (0,0), (2,-4)]
    test_lines = [test_pts, [(x+1, y-1) for x,y in test_pts]]
    test_cards = [py5.Card() for j in range(3)]
    test_name = "my test name"
    
    def testCardInitValues(self):
        """Card should assign the correct init values for all properties."""
        test_rect = self.test_rect
        card = py5.Card(rect=test_rect)
        self.assertEqual(card.rect, test_rect)

    def testContentInitValues(self):
        """Content should assign the correct init values for all properties."""
        test_rect = self.test_rect
        test_kind = py5.Content.KIND_LBL_CONCEPT
        test_rating = py5.Content.RATING_MAX
        test_collapsed = True
        test_title = "my test title"
        test_content = "this is content\n\nand this is more.\n\n\nrtag1: foo bar."

        cont = py5.Content(rect=test_rect, kind=test_kind, rating=test_rating,
                           collapsed=test_collapsed, title=test_title, content=test_content)
        self.assertEqual(cont.rect,  test_rect)
        self.assertEqual(cont.kind,  test_kind)
        self.assertEqual(cont.title, test_title)
        self.assertEqual(cont.rating,    test_rating)
        self.assertEqual(cont.content,   test_content)
        self.assertEqual(cont.collapsed, test_collapsed)

    def testHeaderInitValues(self):
        """Header should assign the correct init values for all properties."""
        test_rect = self.test_rect
        test_header = "my test header"
        head = py5.Header(rect=test_rect, header=test_header)
        self.assertEqual(head.rect, test_rect)
        self.assertEqual(head.header, test_header)

    def testImageInitValues(self):
        """Image should assign the correct init values for all properties."""
        test_rect = self.test_rect
        test_path = "/home/leo/code/1233.bmp"
        test_scale = 0.5

        img = py5.Image(rect=test_rect, path=test_path, scale=test_scale)
        self.assertEqual(img.rect, test_rect)
        self.assertEqual(img.path, test_path)
        self.assertEqual(img.scale, test_scale)

    def testLineInitValues(self):
        """Line should assign the correct init values for all properties."""
        test_colour = (255,255,255,0)
        test_thickness = 15
        test_pts = self.test_pts

        line = py5.Line(colour=test_colour, thickness=test_thickness, pts=test_pts)
        self.assertEqual(line.colour, test_colour)
        self.assertEqual(line.thickness, test_thickness)
        self.assertEqual(line.pts, test_pts)

    def testAnnotationInitValues(self):
        """Annotation should assign the correct init values for all properties."""
        test_lines = self.test_lines

        anno = py5.Annotation(lines=test_lines)
        self.assertEqual(anno.lines, test_lines)

    def testCardGroupInitValues(self):
        """CardGroup should assign the correct init values for all properties."""
        test_members = self.test_members

        grp = py5.CardGroup(members=test_members)
        self.assertEqual(grp.members, test_members)

    def testDeckInitValues(self):
        """Deck should assign the correct init values for all properties."""
        test_name = self.test_name
        test_cards = [py5.Card() for j in range(3)]
        test_members = self.test_members
        test_groups = [py5.CardGroup(members=test_members.append(2*j)) for j in range(3)]

        deck = py5.Deck(name=test_name, cards=test_cards, groups=test_groups)
        self.assertEqual(deck.name, test_name)
        self.assertEqual(deck.cards, test_cards)
        self.assertEqual(deck.groups, test_groups)

    def testAnnotatedDeckInitValues(self):
        """AnnotatedDeck should assign the correct init values for all properties."""
        test_name = self.test_name
        test_cards = self.test_cards
        test_members = self.test_members
        test_groups = [py5.CardGroup(members=test_members.append(2*j)) for j in range(3)]
        test_lines = self.test_lines

        annodk = py5.AnnotatedDeck(name=test_name, cards=test_cards, groups=test_groups, lines=test_lines)
        self.assertEqual(annodk.name, test_name)
        self.assertEqual(annodk.cards, test_cards)
        self.assertEqual(annodk.groups, test_groups)
        self.assertEqual(annodk.annotation.lines, test_lines)

    def testBoxInitValues(self):
        """Box should assign the correct init values for all properties."""
        test_name = self.test_name
        test_path = "/home/leo/research/foobar.aaa"
        test_cards = self.test_cards
        test_decks = [py5.AnnotatedDeck(cards=test_cards) for j in range(5)]

        box = py5.Box(name=test_name, path=test_path, decks=test_decks)
        self.assertEqual(box.name, test_name)
        self.assertEqual(box.path, test_path)
        self.assertEqual(box.decks, test_decks)



class GetSetPub(unittest.TestCase):
    test_id = 3
    test_rect = (1,2,3,4)
    test_members = [-1, 3, 10001]
    test_pts = [(1,2), (3,4), (-1,-1), (0,0), (2,-4)]
    test_lines = [test_pts, [(x+1, y-1) for x,y in test_pts]]
    test_cards = [py5.Card() for j in range(3)]
    test_name = "my test name"

    def testCardGetSetPub(self):
        """Card should publish every call to its property getters."""
        test_id = self.test_id
        test_rect = self.test_rect

        # we haven't subsccribed anything yet so the messages sent when
        # setting default values in the constructor won't be logged
        card = py5.Card()
        topic = card._root

        # lis = listener(topics=["Card." + str(card._id)])
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})        

        # the UPDATE_ID message is sent with the old id
        # we need to subscribe to the messages sent with the new id
        card._id = test_id
        calls[topic + "." + "UPDATE_ID"] +=1
        topic = card._root
        lis.addTopic(topic)
        
        card.rect = test_rect
        calls[topic + "." + "UPDATE_RECT"] +=1

        self.assertEqual(card._id, test_id)
        self.assertEqual(card.rect, test_rect)
        self.assertEqual(calls, lis.calls)

    def testContentGetSetPub(self):
        """Content should publish every call to its property getters."""
        test_id = self.test_id
        test_rect = self.test_rect
        test_kind = py5.Content.KIND_LBL_CONCEPT
        test_rating = py5.Content.RATING_MAX
        test_collapsed = True
        test_title = "my test title"
        test_content = "this is content\nand this is more.\n\ntag1: foo bar."

        cont = py5.Content()
        topic = cont._root
        
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})
        
        cont._id=test_id
        calls[topic + "." + "UPDATE_ID"] += 1
        topic = cont._root
        lis.addTopic(topic)
        
        cont.rect=test_rect
        cont.kind=test_kind
        cont.rating=test_rating
        cont.collapsed=test_collapsed
        cont.title=test_title
        cont.content=test_content
        calls[topic + "." + "UPDATE_RECT"] += 1
        calls[topic + "." + "UPDATE_KIND"] += 1
        calls[topic + "." + "UPDATE_RATING"] += 1
        calls[topic + "." + "UPDATE_COLLAPSED"] += 1
        calls[topic + "." + "UPDATE_TITLE"] += 1
        calls[topic + "." + "UPDATE_CONTENT"] += 1

        self.assertEqual(cont._id,    test_id)
        self.assertEqual(cont.rect,  test_rect)
        self.assertEqual(cont.kind,  test_kind)
        self.assertEqual(cont.title, test_title)
        self.assertEqual(cont.rating,    test_rating)
        self.assertEqual(cont.content,   test_content)
        self.assertEqual(cont.collapsed, test_collapsed)
        self.assertEqual(calls, lis.calls)

    def testHeaderGetSetPub(self):
        """Header should publish every call to its property getters."""
        test_id = self.test_id
        test_rect = self.test_rect
        test_header = "my test header"
        
        head = py5.Header()
        topic = head._root
        
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})

        head._id = test_id
        calls[topic + "." + "UPDATE_ID"] += 1
        topic = head._root
        lis.addTopic(topic)
        
        head.rect =  test_rect
        head.header = test_header
        calls[topic + "." + "UPDATE_RECT"] += 1
        calls[topic + "." + "UPDATE_HEADER"] += 1
        
        self.assertEqual(head._id,   test_id)      
        self.assertEqual(head.rect, test_rect)    
        self.assertEqual(head.header, test_header)
        self.assertEqual(calls, lis.calls)

    def testImageGetSetPub(self):
        """Image should publish every call to its property getters."""
        test_id = self.test_id
        test_rect = self.test_rect
        test_path = "/home/leo/code/1233.bmp"
        test_scale = 0.5

        img = py5.Image()
        topic = img._root

        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})
        
        img._id = test_id
        calls[topic + ".UPDATE_ID"] += 1
        topic = img._root
        lis.addTopic(topic)
        
        img.rect = test_rect
        img.path = test_path
        img.scale = test_scale
        calls[topic + "." + "UPDATE_RECT"] += 1
        calls[topic + "." + "UPDATE_PATH"] += 1
        calls[topic + "." + "UPDATE_SCALE"] += 1
        
        self.assertEqual(img._id,   test_id)
        self.assertEqual(img.rect, test_rect)
        self.assertEqual(img.path, test_path)
        self.assertEqual(img.scale, test_scale)
        self.assertEqual(calls, lis.calls)

    def testAnnotationGetSetPub(self):
        """Annotation should publish every call to its property getters."""
        test_lines = self.test_lines

        anno = py5.Annotation()
        topic = anno._root

        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})
        
        anno.lines = test_lines
        calls[topic + "." + "UPDATE_LINES"] += 1

        self.assertEqual(anno.lines, test_lines)
        self.assertEqual(calls, lis.calls)

    def testCardGroupGetSetPub(self):
        """CardGroup should publish every call to its property getters."""
        test_id = self.test_id
        test_members = self.test_members

        grp = py5.CardGroup()
        topic = grp._root
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})

        grp._id = test_id
        calls[topic + "." + "UPDATE_ID"] += 1
        topic = grp._root
        lis.addTopic(topic)
        
        grp.members = test_members
        calls[topic + "." + "UPDATE_MEMBERS"] += 1

        self.assertEqual(grp._id, test_id)
        self.assertEqual(grp.members, test_members)
        self.assertEqual(calls, lis.calls)

    def testDeckGetSetPub(self):
        """Deck should publish every call to its property getters."""
        test_id = self.test_id
        test_name = self.test_name
        test_cards = [py5.Card() for j in range(3)]
        test_members = self.test_members
        test_groups = [py5.CardGroup(members=test_members.append(2*j)) for j in range(3)]

        deck = py5.Deck()
        topic = deck._root

        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})
        
        deck._id = test_id
        calls[topic + "." + "UPDATE_ID"] += 1
        topic = deck._root
        lis.addTopic(topic)
        
        deck.name = test_name
        deck.cards = test_cards
        deck.groups = test_groups
        calls[topic + "." + "UPDATE_NAME"] += 1
        calls[topic + "." + "UPDATE_CARDS"] += 1
        calls[topic + "." + "UPDATE_GROUPS"] += 1

        self.assertEqual(deck._id, test_id)
        self.assertEqual(deck.name, test_name)
        self.assertEqual(deck.cards, test_cards)
        self.assertEqual(deck.groups, test_groups)
        self.assertEqual(calls, lis.calls)

    def testAnnotatedDeckGetSetPub(self):
        """AnnotatedDeck should publish every call to its property getters."""
        test_id = self.test_id
        test_name = self.test_name
        test_cards = self.test_cards
        test_members = self.test_members
        test_lines = self.test_lines
        test_groups = [py5.CardGroup(members=test_members.append(2*j)) for j in range(3)]

        annodk = py5.AnnotatedDeck()
        topic = annodk._root
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})
        
        annodk._id = test_id
        calls[topic + "." + "UPDATE_ID"] += 1
        topic = annodk._root
        lis.addTopic(topic)
        
        annodk.name = test_name
        annodk.cards = test_cards
        annodk.groups = test_groups
        annodk.annotation.lines = test_lines
        calls[topic + "." + "UPDATE_NAME"] += 1
        calls[topic + "." + "UPDATE_CARDS"] += 1
        calls[topic + "." + "UPDATE_GROUPS"] += 1
        # calls[topic + "." + "UPDATE_LINES"] += 1

        self.assertEqual(annodk._id, test_id)
        self.assertEqual(annodk.name, test_name)
        self.assertEqual(annodk.cards, test_cards)
        self.assertEqual(annodk.groups, test_groups)
        self.assertEqual(annodk.annotation.lines, test_lines)
        self.assertEqual(calls, lis.calls)

    def testBoxGetSetPub(self):
        """Box should publish every call to its property getters."""
        test_id = self.test_id
        test_name = self.test_name
        test_path = "/home/leo/research/foobar.aaa"
        test_cards = self.test_cards
        test_decks = [py5.AnnotatedDeck(cards=test_cards) for j in range(5)]

        box = py5.Box()
        topic = box._root
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})
        
        box._id = test_id
        calls[topic + "." + "UPDATE_ID"] += 1
        topic = box._root
        lis.addTopic(topic)

        box.name = test_name
        box.path = test_path
        box.decks = test_decks
        calls[topic + "." + "UPDATE_NAME"] += 1
        calls[topic + "." + "UPDATE_PATH"] += 1
        calls[topic + "." + "UPDATE_DECKS"] += 1

        self.assertEqual(box.name, test_name)
        self.assertEqual(box.path, test_path)
        self.assertEqual(box.decks, test_decks)
        self.assertEqual(calls, lis.calls)

        

class NonOverlappingAttributes(unittest.TestCase):

    def testCardOverlapping(self):
        """Card objects should not share references to the same data."""
        card1 = py5.Card()
        card2 = py5.Card()
        
        card1.rect = (1,2,3,4)
        card2.rect = (2,3,4,5)
                
        self.assertNotEqual(card1._id, card2._id)
        self.assertNotEqual(card1.rect, card2.rect)

    def testContentOverlapping(self):
        """Content objects should not share references to the same data."""
        cont1 = py5.Content()
        cont2 = py5.Content()
        
        cont2.rect = (0,0,1,0)
        cont1.rect = (1,2,3,1)
        cont2.kind = "C"
        cont1.kind = "F"
        cont2.rating = 0
        cont1.rating = py5.Content.RATING_MAX + 1
        cont2.collapsed = True
        cont1.collapsed = False
        cont2.title = "tit1"
        cont1.title = "tit2"
        cont2.content = "foo bar\ntag: baz."
        cont1.content = "foo bar\ntag2: baz."

        self.assertNotEqual(cont1._id, cont2._id)
        self.assertNotEqual(cont1.rect, cont2.rect)
        self.assertNotEqual(cont1.kind, cont2.kind)
        self.assertNotEqual(cont1.rating,    cont2.rating)
        self.assertNotEqual(cont1.collapsed, cont2.collapsed)
        self.assertNotEqual(cont1.title, cont2.title)
        self.assertNotEqual(cont1.content, cont2.content)

    def testHeaderOverlapping(self):
        """Header objects should not share references to the same data."""
        head1 = py5.Header()
        head2 = py5.Header()
        
        head2.rect = (1,29,1,0)
        head1.rect = (1,20,0,1)
        head2.header = "head1"
        head1.header = "head2"
        
        self.assertNotEqual(head1._id,   head2._id)
        self.assertNotEqual(head1.rect, head2.rect)
        self.assertNotEqual(head1.header, head2.header)

    def testImageOverlapping(self):
        """Image objects should not share references to the same data."""
        img1 = py5.Image()
        img2 = py5.Image()
        
        img2.rect = (1,29,1,0)
        img1.rect = (1,39,1,0)
        img2.scale = 1.5
        img1.scale = 0.25
        img2.path = "/home/leo/"
        img1.path = "/home/leo/code"
        
        self.assertNotEqual(img1._id, img2._id)
        self.assertNotEqual(img1.rect, img2.rect)
        self.assertNotEqual(img1.scale, img2.scale)
        self.assertNotEqual(img1.path, img2.path)

    def testLineOverlapping(self):
        """Line objects should not share references to the same data."""
        line1 = py5.Line()
        line2 = py5.Line()
        
        line2.colour = (15,15,15,0)
        line1.colour = (15,15,10,0)
        line2.thickness = 1
        line1.thickness = 4
        line2.pts = [(1,2), (3,4), (-1,-1), (0,0), (2,-4)]
        line1.pts = [(1,-1), (3,4), (-1,-1), (0,0), (2,-4)]
        
        self.assertNotEqual(line1.colour, line2.colour)
        self.assertNotEqual(line1.thickness, line2.thickness)
        self.assertNotEqual(line1.pts, line2.pts)

    def testAnnotationOverlapping(self):
        """Annotation objects should not share references to the same data."""
        anno1 = py5.Annotation()
        anno2 = py5.Annotation()

        test_pts = [(1,2), (3,4), (-1,-1), (0,0), (2,-4)]
        anno2.lines = [test_pts, [(x+1, y-1) for x,y in test_pts]]
        anno1.lines = [test_pts, [(x-1, y+1) for x,y in test_pts]]
        
        self.assertNotEqual(anno1.lines, anno2.lines)

    def testCardGroupOverlapping(self):
        """CardGroup objects should not share references to the same data."""
        grp1 = py5.CardGroup()
        grp2 = py5.CardGroup()
        
        grp2.members = [-1, 3, 10001, 3]
        grp1.members = [-1, 3, 10001]
        
        self.assertNotEqual(grp1._id, grp2._id)
        self.assertNotEqual(grp1.members, grp2.members)

    def testDeckOverlapping(self):
        """Deck objects should not share references to the same data."""
        deck1 = py5.Deck()
        deck2 = py5.Deck()
        
        deck2.name = "name1"
        deck1.name = "name2"
        deck2.cards = [py5.Card() for j in range(3)]
        deck1.cards = [py5.Card() for j in range(4)]
        test_members = [-1, 3, 10001, 3]
        deck2.groups = [py5.CardGroup(members=test_members.append(2*j)) for j in range(3)]
        deck1.groups = [py5.CardGroup(members=test_members.append(2*j)) for j in range(3)]
        
        self.assertNotEqual(deck1._id, deck2._id)
        self.assertNotEqual(deck1.name, deck2.name)
        self.assertNotEqual(deck1.cards, deck2.cards)
        self.assertNotEqual(deck1.groups, deck2.groups)

    def testAnnotatedDeckOverlapping(self):
        """AnnotatedDeck objects should not share references to the same data."""
        annodk1 = py5.AnnotatedDeck()
        annodk2 = py5.AnnotatedDeck()
        
        annodk2.name = "name1"
        annodk1.name = "name2"
        annodk2.cards = [py5.Card() for j in range(3)]
        annodk1.cards = [py5.Card() for j in range(2)]
        test_members = [-1, 3, 10001, 3]
        annodk2.groups = [py5.CardGroup(members=test_members.append(2*j)) for j in range(3)]
        annodk1.groups = [py5.CardGroup(members=test_members.append(2*j)) for j in range(3)]
        test_pts = [(1,2), (3,4), (-1,-1), (0,0), (2,-4)]
        annodk2.annotation.lines = [test_pts, [(x+1, y-1) for x,y in test_pts]]
        annodk1.annotation.lines = [test_pts, [(x-1, y+1) for x,y in test_pts]]
        
        self.assertNotEqual(annodk1._id, annodk2._id)
        self.assertNotEqual(annodk1.name, annodk2.name)
        self.assertNotEqual(annodk1.cards, annodk2.cards)
        self.assertNotEqual(annodk1.groups, annodk2.groups)
        self.assertNotEqual(annodk1.annotation.lines, annodk2.annotation.lines)

    def testBoxOverlapping(self):
        """Box objects should not share references to the same data."""
        box1 = py5.Box()
        box2 = py5.Box()
        
        box2.name = "name1"
        box1.name = "name2"
        box2.path = "/home/leo/"
        box1.path = "/home/leo/code"
        test_cards = [py5.Card() for j in range(3)]
        test_decks = [py5.AnnotatedDeck(cards=test_cards) for j in range(5)]
        box2.decks = test_decks
        test_decks2 = test_decks[:]
        test_decks2.append(py5.Card())
        box1.decks = test_decks2
        
        self.assertNotEqual(box1.name, box2.name)
        self.assertNotEqual(box1.path, box2.path)
        self.assertNotEqual(box1.decks, box2.decks)




                        
class AddRemove(unittest.TestCase):

    def testCardGroupAddRemove(self):
        """CardGroup Add/Remove should work properly and publish their calls."""
        card = py5.Card()
        grp = py5.CardGroup()
        topic = grp._root
        
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})        

        grp.Add(card)
        calls[topic + "." + "NEW_MEMBER"] += 1
        grp.Remove(card)
        calls[topic + "." + "POP_MEMBER"] += 1

        self.assertEqual(grp.members, [])
        self.assertEqual(calls, lis.calls)

    def testDeckAddRemove(self):
        """Deck Add/Remove should work properly and publish their calls."""
        card = py5.Card()
        group = py5.CardGroup()
        deck = py5.Deck()
        topic = deck._root
        
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})        
        
        deck.AddCard(card)
        deck.RemoveCard(card)
        deck.AddGroup(group)
        deck.RemoveGroup(group)
        calls[topic + "." + "NEW_CARD"] += 1
        calls[topic + "." + "POP_CARD"] += 1
        calls[topic + "." + "NEW_GROUP"] += 1
        calls[topic + "." + "POP_GROUP"] += 1

        self.assertEqual(deck.cards, [])
        self.assertEqual(deck.groups, [])
        self.assertEqual(calls, lis.calls)

    def testAnnotatedDeckAddRemove(self):
        """AnnotatedDeck Add/Remove should work properly and publish their calls."""
        card = py5.Card()
        group = py5.CardGroup()
        annodk = py5.AnnotatedDeck()
        topic = annodk._root
        
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})
        
        annodk.AddCard(card)
        annodk.RemoveCard(card)
        annodk.AddGroup(group)
        annodk.RemoveGroup(group)
        line = py5.Line()
        annodk.annotation.Add(line)
        annodk.annotation.Remove(line)
        calls[topic + "." + "NEW_CARD"] += 1
        calls[topic + "." + "POP_CARD"] += 1
        calls[topic + "." + "NEW_GROUP"] += 1
        calls[topic + "." + "POP_GROUP"] += 1

        self.assertEqual(annodk.cards, [])
        self.assertEqual(annodk.groups, [])
        self.assertEqual(annodk.annotation.lines, [])
        self.assertEqual(calls, lis.calls)

    def testBoxAddRemove(self):
        """Box Add/Remove should work properly and publish their calls."""
        deck = py5.AnnotatedDeck()
        box = py5.Box()
        topic = box._root
        lis = listener(topics=[topic])
        calls = defaultdict(lambda: 0, {})
        
        box.AddDeck(deck)
        calls[topic + "." + "NEW_DECK"] += 1
        box.RemoveDeck(deck)
        calls[topic + "." + "POP_DECK"] += 1

        self.assertEqual(box.decks, [])
        self.assertEqual(calls, lis.calls)

        


class CardMethods(unittest.TestCase):
    test_pt1 = (3,4)
    test_pt2 = (100,23. -123.12299)

    def testPosition(self):
        """Card should set and get the correct position."""
        card = py5.Card()
        
        card.Position = self.test_pt1
        self.assertEqual(card.Position, (card.rect.left, card.rect.top))
        self.assertEqual(card.Position, self.test_pt1)
        
        card.Position = self.test_pt2
        self.assertEqual(card.Position, (card.rect.left, card.rect.top))
        self.assertEqual(card.Position, self.test_pt2)

    def testSize(self):
        """Card should set and get the correct size."""
        card = py5.Card()
        
        card.Size = self.test_pt1
        self.assertEqual(card.Size, (card.rect.width, card.rect.height))
        self.assertEqual(card.Size, self.test_pt1)
        
        card.Size = self.test_pt2
        self.assertEqual(card.Size, (card.rect.width, card.rect.height))
        self.assertEqual(card.Size, self.test_pt2)

    def testMoveBy(self):
        """Card.MoveBy should correctly set position."""
        card = py5.Card()
        orig = card.Position
        p1 = self.test_pt1
        p2 = self.test_pt2
        
        card.MoveBy(*p1)
        self.assertEqual(card.Position, (p1[0] + orig[0], p1[1] + orig[1]))
        
        card.MoveBy(*p1)
        self.assertEqual(card.Position, (2*p1[0] + orig[0], 2*p1[1] + orig[1]))

        card.MoveBy(*p2)
        self.assertEqual(card.Position, (p2[0] + 2*p1[0] + orig[0], p2[1] + 2*p1[1] + orig[1]))

    def testDumpLoad(self):
        """Card.Dump and Load should correctly give and read all info."""
        card = py5.Card()
        
        data = card.Dump()
        self.assertEqual(data["id"], card._id)
        self.assertEqual(list(data["rect"]), list(card.rect))

        data["id"] = 3
        data["rect"] = (1,2,3,4)

        # remember Load doesn't copy the id...
        card.Load(data)
        self.assertEqual(list(data["rect"]), list(card.rect))

        # ...but Clone does
        card.Clone(data)
        self.assertEqual(data["id"], card._id)
        self.assertEqual(list(data["rect"]), list(card.rect))


        
class HeaderMethods(unittest.TestCase):
    
    def testDumpLoad(self):
        """Header.Dump and Load should correctly give and read all info."""
        head = py5.Header()
        
        data = head.Dump()
        self.assertEqual(data["id"], head._id)
        self.assertEqual(list(data["rect"]), list(head.rect))
        self.assertEqual(data["header"], head.header)
        
        data["id"] = 3
        data["rect"] = (1,2,3,4)
        data["header"] = (1,2,3,4)

        head.Load(data)
        self.assertEqual(list(data["rect"]), list(head.rect))
        self.assertEqual(data["header"], head.header)

        head.Clone(data)
        self.assertEqual(data["id"], head._id)
        self.assertEqual(list(data["rect"]), list(head.rect))
        self.assertEqual(data["header"], head.header)


                        
class ContentMethods(unittest.TestCase):
    
    def testDumpLoad(self):
        """Content.Dump and Load should correctly give and read all info."""
        cont = py5.Content()
        
        data = cont.Dump()
        self.assertEqual(data["id"], cont._id)
        self.assertEqual(list(data["rect"]), list(cont.rect))
        self.assertEqual(data["title"], cont.title)
        self.assertEqual(data["kind"], cont.kind)
        self.assertEqual(data["rating"], cont.rating)
        self.assertEqual(data["content"], cont.content)
        self.assertEqual(data["collapsed"], cont.collapsed)
        
        data["id"] = 3
        data["rect"] = (1,2,3,4)

        cont.Load(data)
        self.assertEqual(list(data["rect"]), list(cont.rect))
        self.assertEqual(data["title"], cont.title)
        self.assertEqual(data["kind"], cont.kind)
        self.assertEqual(data["rating"], cont.rating)
        self.assertEqual(data["content"], cont.content)
        self.assertEqual(data["collapsed"], cont.collapsed)

        cont.Clone(data)
        self.assertEqual(data["id"], cont._id)
        self.assertEqual(list(data["rect"]), list(cont.rect))
        self.assertEqual(data["title"], cont.title)
        self.assertEqual(data["kind"], cont.kind)
        self.assertEqual(data["rating"], cont.rating)
        self.assertEqual(data["content"], cont.content)
        self.assertEqual(data["collapsed"], cont.collapsed)

        


class ImageMethods(unittest.TestCase):
    
    def testDumpLoad(self):
        """Image.Dump and Load should correctly give and read all info."""
        img = py5.Image()
        
        data = img.Dump()
        self.assertEqual(data["id"], img._id)
        self.assertEqual(list(data["rect"]), list(img.rect))
        self.assertEqual(data["path"], img.path)
        self.assertEqual(data["scale"], img.scale)
        
        data["id"] = 3
        data["rect"] = (1,2,3,4)
        data["path"] = "/foo/bar/baz"
        data["scale"] = 2.0
        
        img.Load(data)
        self.assertEqual(list(data["rect"]), list(img.rect))
        self.assertEqual(data["path"], img.path)
        self.assertEqual(data["scale"], img.scale)

        img.Clone(data)
        self.assertEqual(data["id"], img._id)
        self.assertEqual(list(data["rect"]), list(img.rect))
        self.assertEqual(data["path"], img.path)
        self.assertEqual(data["scale"], img.scale)
        

### test Deck dump, load



if __name__ == "__main__":
    unittest.main()
