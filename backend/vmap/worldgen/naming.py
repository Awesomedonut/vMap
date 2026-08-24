"""Stage 9-lite: Markov-chain name generator seeded from the world RNG."""

from __future__ import annotations

import numpy as np

TRAINING = [
    "Aeloria", "Westmarch", "Thornwick", "Eldenvale", "Karthmere", "Ravenholm",
    "Silverkeep", "Dunmore", "Ashford", "Blackwater", "Ironhold", "Greymoor",
    "Highgarden", "Stonehaven", "Windermere", "Caldera", "Norwick", "Sunspire",
    "Mistral", "Oakhurst", "Fenwick", "Coldbrook", "Amberfall", "Duskendale",
    "Everton", "Falkirk", "Galenport", "Halloway", "Ivarstead", "Jorvik",
    "Kestrel", "Lynnhaven", "Meridell", "Northolt", "Ormsgate", "Pellinor",
    "Quintessa", "Rosewood", "Selwyn", "Tarnmouth", "Ulverston", "Vantage",
    "Wyndham", "Yarrow", "Zephyria", "Bellhaven", "Cormyr", "Drakemoor",
    "Elsinore", "Farwater", "Glenhollow", "Harrowgate", "Isenfall", "Kingsbury",
    "Larkspur", "Mournwood", "Nightvale", "Oldenburg", "Pinemarch", "Redcliff",
    "Stormwatch", "Thundertop", "Umberlee", "Violetgard", "Whitehall", "Emberlyn",
]


class NameGenerator:
    """Order-2 character Markov chain over the training list."""

    def __init__(self, rng: np.random.Generator):
        self.rng = rng
        self.table: dict[str, list[str]] = {}
        for word in TRAINING:
            w = f"^^{word.lower()}$"
            for i in range(len(w) - 2):
                self.table.setdefault(w[i : i + 2], []).append(w[i + 2])
        self.used: set[str] = set()

    def generate(self) -> str:
        for _ in range(60):
            out, key = [], "^^"
            while True:
                choices = self.table.get(key)
                if not choices:
                    break
                c = choices[int(self.rng.integers(0, len(choices)))]
                if c == "$":
                    break
                out.append(c)
                key = key[1] + c
                if len(out) > 11:
                    break
            name = "".join(out).capitalize()
            if 5 <= len(name) <= 11 and name not in self.used:
                self.used.add(name)
                return name
        # fallback: numbered variant, still deterministic
        name = f"Newhaven{len(self.used) + 1}"
        self.used.add(name)
        return name
