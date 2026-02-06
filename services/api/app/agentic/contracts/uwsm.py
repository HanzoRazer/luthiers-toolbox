"""
User Working Style Model (UWSM) v1

Captures user preferences for agent behavior adaptation.
This is the "personality" layer that enables personalized agent responses.

Design principles:
1. Preferences are probabilistic, not binary
2. Confidence and recency matter (decay over time)
3. Dimensions are orthogonal (can vary independently)
4. Privacy-first: UWSM is local-only by default
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PreferenceDimension(str, Enum):
    """
    Orthogonal dimensions of user working style.

    Each dimension has a value from 0.0 to 1.0:
    - GUIDANCE_DENSITY: 0=minimal hints, 1=detailed guidance
    - INITIATIVE_TOLERANCE: 0=ask first, 1=act autonomously
    - COGNITIVE_LOAD_SENSITIVITY: 0=show everything, 1=minimize info
    - EXPLORATION_STYLE: 0=depth-first, 1=breadth-first
    - RISK_POSTURE: 0=conservative, 1=aggressive
    - FEEDBACK_STYLE: 0=quiet, 1=verbose
    """
    GUIDANCE_DENSITY = "guidance_density"
    INITIATIVE_TOLERANCE = "initiative_tolerance"
    COGNITIVE_LOAD_SENSITIVITY = "cognitive_load_sensitivity"
    EXPLORATION_STYLE = "exploration_style"
    RISK_POSTURE = "risk_posture"
    FEEDBACK_STYLE = "feedback_style"


class DecayConfig(BaseModel):
    """
    Configuration for preference decay over time.

    Old signals should matter less than recent ones.
    This enables the model to adapt to changing user behavior.
    """
    model_config = ConfigDict(extra="forbid")

    half_life_days: float = Field(
        default=30.0,
        gt=0.0,
        description="Days until signal strength halves"
    )
    min_confidence: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Floor for decayed confidence"
    )
    decay_enabled: bool = Field(
        default=True,
        description="Whether decay is active"
    )


class PreferenceSignal(BaseModel):
    """
    A single observed preference signal.

    Signals are accumulated over time to infer preferences.
    """
    model_config = ConfigDict(extra="forbid")

    dimension: PreferenceDimension = Field(
        description="Which dimension this signal informs"
    )
    value: float = Field(
        ge=0.0,
        le=1.0,
        description="Observed value (0.0 to 1.0)"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How confident we are in this signal"
    )
    observed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this signal was observed"
    )
    source: str = Field(
        default="",
        description="What interaction produced this signal"
    )


class DimensionState(BaseModel):
    """
    Current state of a single preference dimension.

    Aggregates multiple signals with decay.
    """
    model_config = ConfigDict(extra="forbid")

    dimension: PreferenceDimension = Field(
        description="Which dimension"
    )
    value: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Current inferred value"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in current value (0=no data)"
    )
    signal_count: int = Field(
        default=0,
        ge=0,
        description="Number of signals contributing"
    )
    last_updated: datetime | None = Field(
        default=None,
        description="When this dimension was last updated"
    )


class UWSMv1(BaseModel):
    """
    User Working Style Model v1.

    Captures and adapts to user preferences across 6 dimensions.
    This model is:
    - Local-only by default (Layer 0 privacy)
    - Probabilistic (values + confidence, not binary)
    - Adaptive (decays old signals, learns from new ones)
    - Orthogonal (dimensions vary independently)

    Example usage:
        uwsm = UWSMv1(user_id="local")
        uwsm.record_signal(PreferenceSignal(
            dimension=PreferenceDimension.GUIDANCE_DENSITY,
            value=0.8,  # User seems to want detailed guidance
            confidence=0.6,
            source="dismissed_minimal_hint"
        ))

        # Agent queries preference
        guidance = uwsm.get_dimension(PreferenceDimension.GUIDANCE_DENSITY)
        if guidance.value > 0.7 and guidance.confidence > 0.3:
            # Provide detailed guidance
            ...
    """
    model_config = ConfigDict(extra="forbid")

    # Identity
    user_id: str = Field(
        default="local",
        description="User identifier (default 'local' for privacy)"
    )
    schema_version: str = Field(
        default="1.0.0",
        description="UWSM schema version"
    )

    # Dimensions
    dimensions: dict[PreferenceDimension, DimensionState] = Field(
        default_factory=lambda: {
            dim: DimensionState(dimension=dim)
            for dim in PreferenceDimension
        },
        description="Current state of each dimension"
    )

    # Signal history (for recomputation)
    signals: list[PreferenceSignal] = Field(
        default_factory=list,
        description="Historical signals (pruned by retention policy)"
    )
    max_signals: int = Field(
        default=1000,
        ge=1,
        description="Maximum signals to retain"
    )

    # Decay configuration
    decay_config: DecayConfig = Field(
        default_factory=DecayConfig,
        description="How preferences decay over time"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this model was created"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="When any dimension was last updated"
    )

    # Privacy
    privacy_layer: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Privacy layer (0=local-only by default)"
    )
    sync_enabled: bool = Field(
        default=False,
        description="Whether this model syncs to cloud (opt-in)"
    )

    def get_dimension(self, dim: PreferenceDimension) -> DimensionState:
        """Get current state of a dimension."""
        return self.dimensions.get(dim, DimensionState(dimension=dim))

    def record_signal(self, signal: PreferenceSignal) -> None:
        """
        Record a new preference signal.

        Updates the dimension state and adds to history.
        Prunes old signals if over max_signals.
        """
        # Add to history
        self.signals.append(signal)
        if len(self.signals) > self.max_signals:
            self.signals = self.signals[-self.max_signals:]

        # Update dimension (simplified - production would apply decay)
        dim_state = self.dimensions.get(
            signal.dimension,
            DimensionState(dimension=signal.dimension)
        )

        # Weighted average with new signal
        if dim_state.signal_count == 0:
            new_value = signal.value
            new_confidence = signal.confidence
        else:
            # Simple weighted average (production would use decay)
            total_weight = dim_state.confidence + signal.confidence
            if total_weight > 0:
                new_value = (
                    dim_state.value * dim_state.confidence +
                    signal.value * signal.confidence
                ) / total_weight
                new_confidence = min(1.0, total_weight / 2)
            else:
                new_value = signal.value
                new_confidence = signal.confidence

        self.dimensions[signal.dimension] = DimensionState(
            dimension=signal.dimension,
            value=new_value,
            confidence=new_confidence,
            signal_count=dim_state.signal_count + 1,
            last_updated=datetime.utcnow()
        )
        self.last_updated = datetime.utcnow()
