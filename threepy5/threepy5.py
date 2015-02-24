# -*- coding: utf-8 -*-
"""
Data model for note taking application `threepy5`.
"""

class Card(object):
    def __init__(self, idn):
        """Constructor.

        * `idn: ` this `Card`'s identification number.
        """
        self.id = idn
