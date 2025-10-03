"""
ML enhancer for damage predictions
Currently a simple heuristic model that mimics learned adjustments
"""

from typing import Dict, Any

class DamageMLEnhancer:
	"""Applies ML-based adjustments to damage assessment outputs"""

	def enhance(self, features: Dict[str, Any], damage: Dict[str, Any]) -> Dict[str, Any]:
		"""Return adjusted damage based on input features and base damage.
		features includes asteroid and impact_result summaries.
		"""
		adjusted = dict(damage)

		energy_mt = features.get("energy_megatons", 0.0)
		terrain = features.get("terrain_type", "land")
		population_density = features.get("population_density", 0.0)

		# Example adjustments as if learned from data
		# Higher population density tends to increase injuries relative to casualties
		injury_multiplier = 1.0 + min(1.0, population_density / 20000.0)
		adjusted["injured_count"] = int(adjusted["injured_count"] * injury_multiplier)

		# Urban terrains often have better emergency response reducing casualties ~10%
		if terrain == "urban":
			adjusted["estimated_casualties"] = max(0, int(adjusted["estimated_casualties"] * 0.9))

		# Extremely high energy events increase displacement nonlinearly
		if energy_mt > 100:
			adjusted["displaced_count"] = int(adjusted["displaced_count"] * 1.25)

		# Recompute economic totals proportionally for simplicity
		human_delta = (
			adjusted["estimated_casualties"] * 1_000_000
			+ adjusted["injured_count"] * 100_000
			+ adjusted["displaced_count"] * 50_000
		)
		# Keep infra/env costs unchanged for this simple enhancer
		infra = damage.get("infrastructure_damage_cost", 0.0)
		env = damage.get("environmental_impact_score", 0.0) * 1e9
		adjusted["total_economic_cost"] = human_delta + infra + env

		return adjusted

ml_enhancer = DamageMLEnhancer()
