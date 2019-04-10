"""
Generate cards JSON from APK CSV source.
"""

import csv
import logging
import os
import re

from .base import BaseGen
from .util import camelcase_split

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Cards(BaseGen):
    def __init__(self, config):
        super().__init__(config)

    def arena_id(self, key):
        """Return arena integer id by arena key."""
        csv_path = os.path.join(self.config.csv.base, self.config.csv.path.arenas)
        with open(csv_path) as f:
            texts_reader = csv.DictReader(f)
            for row in texts_reader:
                if row['Name'] == key:
                    return int(row['Arena'])
        return None

    def run(self):
        """Generate all jsons"""
        self.make_cards()

    def make_cards(self):
        """Generate cards.json"""

        cards = []
        card_num = 0

        card_keys = []

        def card_type(card_config, card_num):
            """make card dicts by type."""
            csv_path = os.path.join(self.config.csv.base, card_config.csv)

            with open(csv_path, encoding="utf8") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i > 0:
                        card_num += 1
                        process = True
                        if row['NotInUse']:
                            process = False
                        elif row['Name'].lower().startswith('notinuse'):
                            process = False
                        if process:
                            name_en = self.text(row['TID'], 'EN')
                            if name_en == '':
                                name_en = row['Name']

                            if name_en is not None:
                                name_strip = re.sub('[.\-]', '', name_en)
                                ccs = camelcase_split(name_strip)
                                key = '-'.join(s.lower() for s in ccs)
                                # card_key = '_'.join(s.lower() for s in ccs)
                                decklink = card_config.sckey.format(i - 1)
                                elixir = row.get('ManaCost')
                                if elixir is not None:
                                    elixir = int(elixir)
                                card = {
                                    'key': key,
                                    'name': name_en,
                                    'elixir': elixir,
                                    'type': card_config.type,
                                    'rarity': row['Rarity'],
                                    'arena': self.arena_id(row['UnlockArena']),
                                    'description': self.text(row['TID_INFO'], 'EN'),
                                    'id': int(decklink)
                                }

                                # skip unreleased cards
                                if key in ['wolf-rider', 'prison-goblin']:
                                    continue

                                # ensure unique keys — dev builds have non unique keys
                                if key not in card_keys:
                                    card_keys.append(key)
                                    cards.append(card)
                                    logger.info(card)
                                else:
                                    logger.warning( 'Duplicate card key: %s, skipping...', key )
            return card_num

        for card_config in self.config.cards:
            card_num = card_type(card_config, card_num)

        json_path = os.path.join(self.config.json.base, self.config.json.cards)

        self.save_json(cards, json_path)
