"""
Latin American String Instruments Classifier
=============================================

Unified classifier for Latin American plucked string instruments.

Supported Instruments:
- Venezuelan Cuatro (4 strings, tenor range)
- Puerto Rican Cuatro (10 strings, 5 courses)
- Colombian Tiple (12 strings, 4 courses)
- Requinto (6 strings, smaller guitar)
- Charango (10 strings, 5 courses, Andean)
- Bandola (various configurations)

Author: The Production Shop
Version: 4.0.0-alpha
"""

from .classifier import LatinAmericanStringsClassifier
from .instruments import (
    VenezuelanCuatro,
    PuertoRicanCuatro,
    ColombianTiple,
    Requinto,
    Charango,
    Bandola,
    InstrumentProfile
)

__all__ = [
    'LatinAmericanStringsClassifier',
    'VenezuelanCuatro',
    'PuertoRicanCuatro',
    'ColombianTiple',
    'Requinto',
    'Charango',
    'Bandola',
    'InstrumentProfile'
]

__version__ = '4.0.0-alpha'
