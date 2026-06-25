from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

class Tier(Enum):
    A='A'
    B='B'
    C='C'

class Position(Enum):
    P='P'
    C='C'
    FIRST='1B'
    SECOND='2B'
    THIRD='3B'
    SHORT='SS'
    LF='LF'
    LCF='LCF'
    RCF='RCF'
    RF='RF'
    BENCH='BENCH'

@dataclass
class Player:
    name:str
    tier:Tier
    pitcher:bool=False
    catcher:bool=False
    coach_kid:bool=False
    new_player:bool=False
    active:bool=True

@dataclass
class Assignment:
    inning:int
    position:Position

@dataclass
class Lineup:
    assignments:Dict[str,List[Assignment]]=field(default_factory=dict)
