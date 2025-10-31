"""
Tonewood database with properties and characteristics.
"""

from typing import Dict, List, Optional
from .properties import WoodProperties, AcousticProperties


class Wood:
    """Represents a wood species with its properties."""

    def __init__(
        self,
        name: str,
        scientific_name: str,
        properties: WoodProperties,
        acoustics: AcousticProperties,
        common_uses: List[str],
        description: str = "",
    ):
        """
        Initialize wood species.
        
        Args:
            name: Common name
            scientific_name: Scientific name
            properties: Physical wood properties
            acoustics: Acoustic properties
            common_uses: List of common uses in lutherie
            description: Additional description
        """
        self.name = name
        self.scientific_name = scientific_name
        self.properties = properties
        self.acoustics = acoustics
        self.common_uses = common_uses
        self.description = description

    def __repr__(self) -> str:
        return f"Wood('{self.name}', {self.common_uses})"


class TonewoodDatabase:
    """Database of tonewood species and their properties."""

    def __init__(self):
        """Initialize tonewood database."""
        self.woods: Dict[str, Wood] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default tonewood data."""

        # Mahogany
        self.add_wood(
            Wood(
                name="Mahogany",
                scientific_name="Swietenia macrophylla",
                properties=WoodProperties(
                    density=550,  # kg/m³
                    hardness=800,  # Janka
                    stiffness=10.0,  # GPa
                    workability="good",
                ),
                acoustics=AcousticProperties(
                    frequency_response="warm",
                    resonance="medium",
                    damping="medium",
                    tonal_character="warm, balanced, good midrange",
                ),
                common_uses=["body", "neck"],
                description="Classic choice for guitar bodies and necks. Warm tone with good sustain.",
            )
        )

        # Maple
        self.add_wood(
            Wood(
                name="Maple",
                scientific_name="Acer saccharum",
                properties=WoodProperties(
                    density=710,
                    hardness=1450,
                    stiffness=12.6,
                    workability="good",
                ),
                acoustics=AcousticProperties(
                    frequency_response="bright",
                    resonance="high",
                    damping="low",
                    tonal_character="bright, clear, excellent sustain",
                ),
                common_uses=["neck", "body", "top"],
                description="Bright tonal response. Popular for necks and figured tops.",
            )
        )

        # Rosewood
        self.add_wood(
            Wood(
                name="Rosewood",
                scientific_name="Dalbergia latifolia",
                properties=WoodProperties(
                    density=850,
                    hardness=1780,
                    stiffness=11.5,
                    workability="moderate",
                ),
                acoustics=AcousticProperties(
                    frequency_response="rich",
                    resonance="high",
                    damping="low",
                    tonal_character="rich bass, clear trebles, complex overtones",
                ),
                common_uses=["fretboard", "back_and_sides"],
                description="Premium tonewood with rich, complex tone. Traditional fretboard choice.",
            )
        )

        # Ebony
        self.add_wood(
            Wood(
                name="Ebony",
                scientific_name="Diospyros ebenum",
                properties=WoodProperties(
                    density=1120,
                    hardness=3220,
                    stiffness=15.0,
                    workability="difficult",
                ),
                acoustics=AcousticProperties(
                    frequency_response="bright",
                    resonance="medium",
                    damping="high",
                    tonal_character="tight, articulate, bright attack",
                ),
                common_uses=["fretboard"],
                description="Extremely dense and hard. Provides bright, articulate tone.",
            )
        )

        # Spruce
        self.add_wood(
            Wood(
                name="Spruce",
                scientific_name="Picea sitchensis",
                properties=WoodProperties(
                    density=450,
                    hardness=510,
                    stiffness=11.0,
                    workability="excellent",
                ),
                acoustics=AcousticProperties(
                    frequency_response="balanced",
                    resonance="very high",
                    damping="low",
                    tonal_character="clear, articulate, excellent projection",
                ),
                common_uses=["acoustic_top"],
                description="Standard choice for acoustic guitar tops. Excellent resonance.",
            )
        )

        # Alder
        self.add_wood(
            Wood(
                name="Alder",
                scientific_name="Alnus rubra",
                properties=WoodProperties(
                    density=530,
                    hardness=590,
                    stiffness=9.5,
                    workability="excellent",
                ),
                acoustics=AcousticProperties(
                    frequency_response="balanced",
                    resonance="medium",
                    damping="medium",
                    tonal_character="balanced, even response across frequencies",
                ),
                common_uses=["body"],
                description="Popular electric guitar body wood. Lightweight and balanced.",
            )
        )

        # Ash
        self.add_wood(
            Wood(
                name="Ash",
                scientific_name="Fraxinus americana",
                properties=WoodProperties(
                    density=670,
                    hardness=1320,
                    stiffness=12.0,
                    workability="good",
                ),
                acoustics=AcousticProperties(
                    frequency_response="bright",
                    resonance="high",
                    damping="low",
                    tonal_character="snappy attack, bright highs, good sustain",
                ),
                common_uses=["body"],
                description="Bright, resonant tone with good attack. Traditional Telecaster wood.",
            )
        )

        # Walnut
        self.add_wood(
            Wood(
                name="Walnut",
                scientific_name="Juglans nigra",
                properties=WoodProperties(
                    density=660,
                    hardness=1010,
                    stiffness=11.6,
                    workability="good",
                ),
                acoustics=AcousticProperties(
                    frequency_response="warm",
                    resonance="medium",
                    damping="medium",
                    tonal_character="warm, balanced, good midrange definition",
                ),
                common_uses=["body", "neck"],
                description="Similar to mahogany but slightly brighter. Beautiful grain.",
            )
        )

    def add_wood(self, wood: Wood) -> None:
        """Add a wood species to the database."""
        self.woods[wood.name.lower()] = wood

    def get_wood(self, name: str) -> Optional[Wood]:
        """Get a wood species by name."""
        return self.woods.get(name.lower())

    def list_woods(self) -> List[str]:
        """List all wood species names."""
        return sorted(self.woods.keys())

    def find_by_use(self, use: str) -> List[Wood]:
        """
        Find woods suitable for a specific use.
        
        Args:
            use: Use case (e.g., 'body', 'neck', 'fretboard')
            
        Returns:
            List of suitable wood species
        """
        return [
            wood
            for wood in self.woods.values()
            if use.lower() in [u.lower() for u in wood.common_uses]
        ]

    def find_by_property(
        self, property_name: str, min_value: float, max_value: float
    ) -> List[Wood]:
        """
        Find woods within a property range.
        
        Args:
            property_name: Property to filter by ('density', 'hardness', 'stiffness')
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            List of matching wood species
        """
        results = []
        for wood in self.woods.values():
            value = getattr(wood.properties, property_name, None)
            if value is not None and min_value <= value <= max_value:
                results.append(wood)
        return results

    def compare_woods(self, name1: str, name2: str) -> Dict:
        """
        Compare two wood species.
        
        Args:
            name1: First wood name
            name2: Second wood name
            
        Returns:
            Comparison dict
        """
        wood1 = self.get_wood(name1)
        wood2 = self.get_wood(name2)

        if not wood1 or not wood2:
            return {}

        return {
            "wood1": {
                "name": wood1.name,
                "density": wood1.properties.density,
                "hardness": wood1.properties.hardness,
                "stiffness": wood1.properties.stiffness,
                "tone": wood1.acoustics.tonal_character,
            },
            "wood2": {
                "name": wood2.name,
                "density": wood2.properties.density,
                "hardness": wood2.properties.hardness,
                "stiffness": wood2.properties.stiffness,
                "tone": wood2.acoustics.tonal_character,
            },
        }

    def __repr__(self) -> str:
        return f"TonewoodDatabase({len(self.woods)} species)"
