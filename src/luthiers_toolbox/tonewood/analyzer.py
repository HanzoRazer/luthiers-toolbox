"""
Tonewood analysis and recommendation tools.
"""

from typing import List, Dict, Optional
from .database import TonewoodDatabase, Wood
from .properties import TonalProfile


class TonewoodAnalyzer:
    """Analyzes and recommends tonewoods for guitar building."""

    def __init__(self):
        """Initialize analyzer with tonewood database."""
        self.database = TonewoodDatabase()

    def analyze_wood_combination(
        self,
        body_wood: str,
        neck_wood: str,
        fretboard_wood: str,
    ) -> Optional[TonalProfile]:
        """
        Analyze a combination of woods and predict tonal characteristics.
        
        Args:
            body_wood: Body wood name
            neck_wood: Neck wood name
            fretboard_wood: Fretboard wood name
            
        Returns:
            TonalProfile or None if woods not found
        """
        body = self.database.get_wood(body_wood)
        neck = self.database.get_wood(neck_wood)
        fretboard = self.database.get_wood(fretboard_wood)

        if not all([body, neck, fretboard]):
            return None

        # Analyze overall character (body has most influence)
        body_response = body.acoustics.frequency_response
        overall = self._determine_overall_character(body_response)

        # Bass response (influenced by body and neck)
        bass = self._analyze_bass_response(body, neck)

        # Midrange (balanced by all three)
        mids = self._analyze_midrange_response(body, neck, fretboard)

        # Treble (influenced by fretboard most)
        treble = self._analyze_treble_response(body, fretboard)

        # Sustain (influenced by density and resonance)
        sustain = self._analyze_sustain(body, neck)

        return TonalProfile(
            body_wood=body.name,
            neck_wood=neck.name,
            fretboard_wood=fretboard.name,
            overall_character=overall,
            bass_response=bass,
            midrange_response=mids,
            treble_response=treble,
            sustain=sustain,
        )

    def _determine_overall_character(self, body_response: str) -> str:
        """Determine overall tonal character."""
        character_map = {
            "warm": "Warm and smooth with good balance",
            "bright": "Bright and articulate with excellent clarity",
            "balanced": "Well-balanced across all frequencies",
            "rich": "Rich and complex with strong harmonics",
        }
        return character_map.get(body_response, "Balanced tonal response")

    def _analyze_bass_response(self, body: Wood, neck: Wood) -> str:
        """Analyze bass response."""
        # Heavier woods = more bass
        avg_density = (body.properties.density + neck.properties.density) / 2

        if avg_density > 750:
            return "Strong and full"
        elif avg_density > 600:
            return "Solid and balanced"
        else:
            return "Tight and focused"

    def _analyze_midrange_response(
        self, body: Wood, neck: Wood, fretboard: Wood
    ) -> str:
        """Analyze midrange response."""
        # Look at frequency responses
        responses = [
            body.acoustics.frequency_response,
            neck.acoustics.frequency_response,
            fretboard.acoustics.frequency_response,
        ]

        warm_count = sum(1 for r in responses if r == "warm")
        bright_count = sum(1 for r in responses if r == "bright")

        if warm_count >= 2:
            return "Warm and full"
        elif bright_count >= 2:
            return "Clear and present"
        else:
            return "Balanced and articulate"

    def _analyze_treble_response(self, body: Wood, fretboard: Wood) -> str:
        """Analyze treble response."""
        # Fretboard has more influence on treble
        fb_response = fretboard.acoustics.frequency_response

        if fb_response == "bright":
            return "Bright and cutting"
        elif fb_response == "warm":
            return "Smooth and refined"
        else:
            return "Clear and balanced"

    def _analyze_sustain(self, body: Wood, neck: Wood) -> str:
        """Analyze sustain characteristics."""
        # Higher density and resonance = better sustain
        body_resonance = body.acoustics.get_resonance_score()
        neck_density = neck.properties.density

        if body_resonance > 0.7 and neck_density > 650:
            return "Excellent sustain"
        elif body_resonance > 0.5 or neck_density > 550:
            return "Good sustain"
        else:
            return "Moderate sustain"

    def recommend_for_style(self, style: str) -> Dict[str, List[str]]:
        """
        Recommend woods for a playing style.
        
        Args:
            style: Playing style ('blues', 'rock', 'jazz', 'metal', 'acoustic')
            
        Returns:
            Dict with recommendations for body, neck, and fretboard
        """
        recommendations = {
            "blues": {
                "body": ["alder", "ash", "mahogany"],
                "neck": ["maple", "mahogany"],
                "fretboard": ["rosewood", "maple"],
                "description": "Warm, singing tone with good sustain",
            },
            "rock": {
                "body": ["mahogany", "ash"],
                "neck": ["maple"],
                "fretboard": ["rosewood", "ebony"],
                "description": "Powerful, aggressive tone with clarity",
            },
            "jazz": {
                "body": ["mahogany", "maple"],
                "neck": ["mahogany", "maple"],
                "fretboard": ["ebony", "rosewood"],
                "description": "Warm, smooth tone with complex harmonics",
            },
            "metal": {
                "body": ["mahogany", "ash"],
                "neck": ["maple"],
                "fretboard": ["ebony"],
                "description": "Tight, articulate tone with fast attack",
            },
            "acoustic": {
                "body": ["mahogany", "rosewood"],
                "neck": ["mahogany"],
                "fretboard": ["rosewood", "ebony"],
                "top": ["spruce"],
                "description": "Resonant and balanced",
            },
        }

        return recommendations.get(style.lower(), {})

    def find_alternatives(self, wood_name: str, criteria: str = "tone") -> List[str]:
        """
        Find alternative woods similar to the specified wood.
        
        Args:
            wood_name: Wood to find alternatives for
            criteria: 'tone', 'density', 'hardness'
            
        Returns:
            List of alternative wood names
        """
        wood = self.database.get_wood(wood_name)
        if not wood:
            return []

        alternatives = []

        if criteria == "tone":
            # Find woods with similar tonal character
            target_response = wood.acoustics.frequency_response
            for w in self.database.woods.values():
                if (
                    w.name != wood.name
                    and w.acoustics.frequency_response == target_response
                ):
                    alternatives.append(w.name)

        elif criteria == "density":
            # Find woods with similar density (±15%)
            target = wood.properties.density
            margin = target * 0.15
            alternatives_woods = self.database.find_by_property(
                "density", target - margin, target + margin
            )
            alternatives = [
                w.name for w in alternatives_woods if w.name != wood.name
            ]

        elif criteria == "hardness":
            # Find woods with similar hardness (±20%)
            target = wood.properties.hardness
            margin = target * 0.2
            alternatives_woods = self.database.find_by_property(
                "hardness", target - margin, target + margin
            )
            alternatives = [
                w.name for w in alternatives_woods if w.name != wood.name
            ]

        return alternatives

    def __repr__(self) -> str:
        return f"TonewoodAnalyzer({len(self.database.woods)} species)"
