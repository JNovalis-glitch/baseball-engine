"""Core coaching philosophy and configurable engine rules."""
from dataclasses import dataclass

@dataclass(frozen=True)
class EngineRules:
    innings:int=6
    players_on_field:int=10
    bench_per_inning:int=2
    no_new_player_bench_first:bool=True
    no_consecutive_outfield:bool=True
    max_bench_per_player:int=1
    coach_pitch_innings:tuple=(1,2,5,6)
    kid_pitch_innings:tuple=(3,4)
    prioritize_defense_coach_pitch:bool=True
    prioritize_development_kid_pitch:bool=True
    strong_lcf:bool=True
    first_base_prefers_tier_a:bool=True
    diversify_development_positions:bool=True
    max_same_outfield_position_per_player:int=1
    prefer_corner_outfield_for_development:bool=True
    prefer_third_base_development_reps:bool=True

DEFAULT_RULES=EngineRules()
