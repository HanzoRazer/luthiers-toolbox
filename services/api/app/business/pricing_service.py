"""
Pricing Service — Pricing strategy and recommendations.

Helps luthiers answer: "What should I charge for this guitar?"
"""
from typing import List, Optional, Dict
from datetime import datetime, timezone

from .schemas import (
    PricingStrategy,
    CompetitorPrice,
    COGSBreakdown,
)


class PricingService:
    """
    Pricing strategy calculator.

    Supports multiple pricing models:
    - Cost-plus: COGS + markup percentage
    - Market-based: Aligned with competitor pricing
    - Value-based: What the market will bear

    Responsibilities:
    - Calculate optimal pricing
    - Analyze competitor landscape
    - Recommend positioning
    - Protect margins
    """

    # Market positioning thresholds
    POSITION_THRESHOLDS = {
        "below_market": -0.10,  # >10% below average
        "at_market": 0.10,     # Within 10% of average
        "above_market": 0.10,  # >10% above average
    }

    # Default competitor data (user should customize)
    DEFAULT_COMPETITORS: List[CompetitorPrice] = [
        CompetitorPrice(
            competitor_name="Gibson",
            instrument_type="acoustic_dreadnought",
            price=2499.0,
            quality_tier="premium",
        ),
        CompetitorPrice(
            competitor_name="Martin",
            instrument_type="acoustic_dreadnought",
            price=2799.0,
            quality_tier="premium",
        ),
        CompetitorPrice(
            competitor_name="Taylor",
            instrument_type="acoustic_dreadnought",
            price=1999.0,
            quality_tier="premium",
        ),
        CompetitorPrice(
            competitor_name="Collings",
            instrument_type="acoustic_dreadnought",
            price=4500.0,
            quality_tier="custom",
        ),
        CompetitorPrice(
            competitor_name="Santa Cruz",
            instrument_type="acoustic_dreadnought",
            price=5500.0,
            quality_tier="custom",
        ),
        CompetitorPrice(
            competitor_name="Bourgeois",
            instrument_type="acoustic_dreadnought",
            price=6000.0,
            quality_tier="custom",
        ),
        CompetitorPrice(
            competitor_name="Yamaha",
            instrument_type="acoustic_dreadnought",
            price=499.0,
            quality_tier="entry",
        ),
        CompetitorPrice(
            competitor_name="Epiphone",
            instrument_type="acoustic_dreadnought",
            price=399.0,
            quality_tier="entry",
        ),
    ]

    def __init__(
        self,
        competitors: Optional[List[CompetitorPrice]] = None,
        default_markup_pct: float = 100.0,
        minimum_margin_pct: float = 30.0,
    ):
        """
        Initialize pricing service.

        Args:
            competitors: Competitor pricing data
            default_markup_pct: Default markup over COGS
            minimum_margin_pct: Minimum acceptable margin
        """
        self.competitors = competitors or self.DEFAULT_COMPETITORS
        self.default_markup_pct = default_markup_pct
        self.minimum_margin_pct = minimum_margin_pct

    def calculate_pricing(
        self,
        cogs: float,
        instrument_name: str,
        instrument_type: str = "acoustic_dreadnought",
        target_tier: str = "custom",
        custom_markup_pct: Optional[float] = None,
    ) -> PricingStrategy:
        """
        Calculate pricing strategy for an instrument.

        Args:
            cogs: Cost of Goods Sold
            instrument_name: Name of the instrument
            instrument_type: Type for competitor comparison
            target_tier: Quality tier to compete in
            custom_markup_pct: Override default markup

        Returns:
            Complete PricingStrategy
        """
        markup_pct = custom_markup_pct or self.default_markup_pct
        notes: List[str] = []

        # Cost-plus pricing
        cost_plus_price = cogs * (1 + markup_pct / 100)

        # Market-based pricing
        market_data = self._analyze_market(instrument_type, target_tier)
        market_based_price = market_data.get("average_price")
        market_position = self._determine_position(cost_plus_price, market_based_price)

        # Value-based pricing (heuristic: custom tier = 2x premium)
        value_based_price = None
        value_justification = None

        if target_tier == "custom":
            # Custom builders can charge premium
            tier_prices = self._get_tier_prices(instrument_type)
            premium_avg = tier_prices.get("premium", cost_plus_price)
            value_based_price = premium_avg * 1.5  # 50% above premium
            value_justification = (
                "Custom, hand-built instruments command premium pricing. "
                f"Premium brands average ${premium_avg:.0f}. "
                "Custom builders typically price 50-100% above."
            )
            notes.append(f"Custom tier target: ${value_based_price:.0f}")

        # Determine recommended price
        recommended_price = self._recommend_price(
            cogs=cogs,
            cost_plus=cost_plus_price,
            market_based=market_based_price,
            value_based=value_based_price,
            target_tier=target_tier,
        )

        # Calculate margins
        recommended_margin = recommended_price - cogs
        recommended_margin_pct = (recommended_margin / recommended_price) * 100

        # Margin warnings
        if recommended_margin_pct < self.minimum_margin_pct:
            notes.append(
                f"WARNING: Margin {recommended_margin_pct:.1f}% is below "
                f"minimum {self.minimum_margin_pct}%. Consider raising price."
            )

        # Market positioning notes
        if market_position == "below_market":
            notes.append(
                "Price is below market average. Good for market entry, "
                "but may signal lower quality."
            )
        elif market_position == "above_market":
            notes.append(
                "Price is above market average. Ensure value proposition "
                "justifies premium."
            )

        return PricingStrategy(
            instrument_name=instrument_name,
            cogs=cogs,
            cost_plus_price=round(cost_plus_price, 2),
            cost_plus_markup_pct=markup_pct,
            market_based_price=round(market_based_price, 2) if market_based_price else None,
            market_position=market_position,
            value_based_price=round(value_based_price, 2) if value_based_price else None,
            value_justification=value_justification,
            recommended_price=round(recommended_price, 2),
            recommended_margin=round(recommended_margin, 2),
            recommended_margin_pct=round(recommended_margin_pct, 1),
            notes=notes,
        )

    def _analyze_market(
        self,
        instrument_type: str,
        target_tier: str,
    ) -> Dict[str, float]:
        """Analyze competitor pricing for a segment."""
        relevant = [
            c for c in self.competitors
            if c.instrument_type == instrument_type
            and c.quality_tier == target_tier
        ]

        if not relevant:
            # Fall back to all competitors of this type
            relevant = [
                c for c in self.competitors
                if c.instrument_type == instrument_type
            ]

        if not relevant:
            return {"average_price": None, "min_price": None, "max_price": None}

        prices = [c.price for c in relevant]

        return {
            "average_price": sum(prices) / len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "count": len(prices),
        }

    def _get_tier_prices(
        self,
        instrument_type: str,
    ) -> Dict[str, float]:
        """Get average prices by tier for an instrument type."""
        tier_prices: Dict[str, List[float]] = {}

        for c in self.competitors:
            if c.instrument_type == instrument_type:
                if c.quality_tier not in tier_prices:
                    tier_prices[c.quality_tier] = []
                tier_prices[c.quality_tier].append(c.price)

        return {
            tier: sum(prices) / len(prices)
            for tier, prices in tier_prices.items()
        }

    def _determine_position(
        self,
        price: float,
        market_avg: Optional[float],
    ) -> Optional[str]:
        """Determine market position relative to average."""
        if not market_avg:
            return None

        ratio = (price - market_avg) / market_avg

        if ratio < self.POSITION_THRESHOLDS["below_market"]:
            return "below_market"
        elif ratio > self.POSITION_THRESHOLDS["above_market"]:
            return "above_market"
        else:
            return "at_market"

    def _recommend_price(
        self,
        cogs: float,
        cost_plus: float,
        market_based: Optional[float],
        value_based: Optional[float],
        target_tier: str,
    ) -> float:
        """
        Recommend optimal price based on all inputs.

        Logic:
        1. Never go below cost_plus (protect margin)
        2. For custom tier, lean toward value_based
        3. For other tiers, balance cost_plus and market
        """
        minimum_price = cogs * (1 + self.minimum_margin_pct / 100)

        if target_tier == "custom" and value_based:
            # Custom: go for value pricing
            return max(value_based, minimum_price)

        if market_based:
            # Balance between cost-plus and market
            blended = (cost_plus + market_based) / 2
            return max(blended, minimum_price)

        return max(cost_plus, minimum_price)

    def add_competitor(self, competitor: CompetitorPrice) -> None:
        """Add a competitor to the database."""
        self.competitors.append(competitor)

    def get_competitor_summary(
        self,
        instrument_type: Optional[str] = None,
    ) -> Dict[str, any]:
        """Get summary of competitor landscape."""
        relevant = self.competitors
        if instrument_type:
            relevant = [c for c in relevant if c.instrument_type == instrument_type]

        if not relevant:
            return {"count": 0}

        prices = [c.price for c in relevant]
        tiers = set(c.quality_tier for c in relevant)

        return {
            "count": len(relevant),
            "average_price": sum(prices) / len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "tiers": list(tiers),
        }
