"""
Blueprint Instrument Classifiers
================================

ML-assisted classification system for identifying instrument types from blueprints.

Classifier Families:
- latin_american: Cuatro, Tiple, Requinto, Charango, Bandola
- (future) acoustic_guitar: Dreadnought, OM, 000, Parlor, Jumbo
- (future) electric_guitar: Stratocaster, Telecaster, Les Paul, etc.
- (future) mandolin: A-style, F-style, Bouzouki

Author: Luthier's Toolbox
Version: 4.0.0-alpha
"""

from .latin_american import LatinAmericanStringsClassifier

__all__ = [
    'LatinAmericanStringsClassifier'
]

__version__ = '4.0.0-alpha'
