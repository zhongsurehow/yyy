# src/solar_term.py
from dataclasses import dataclass
from typing import List, Literal

DunType = Literal["YANG", "YIN"]

@dataclass(frozen=True)
class SolarTerm:
    name: str
    dun: DunType

# Full cycle of 24 solar terms, starting from the beginning of the Yang Dun cycle
SOLAR_TERMS_CYCLE: List[SolarTerm] = [
    # Yang Dun Cycle (Winter Solstice to before Summer Solstice)
    SolarTerm("冬至", "YANG"),
    SolarTerm("小寒", "YANG"),
    SolarTerm("大寒", "YANG"),
    SolarTerm("立春", "YANG"),
    SolarTerm("雨水", "YANG"),
    SolarTerm("惊蛰", "YANG"),
    SolarTerm("春分", "YANG"),
    SolarTerm("清明", "YANG"),
    SolarTerm("谷雨", "YANG"),
    SolarTerm("立夏", "YANG"),
    SolarTerm("小满", "YANG"),
    SolarTerm("芒种", "YANG"),
    # Yin Dun Cycle (Summer Solstice to before Winter Solstice)
    SolarTerm("夏至", "YIN"),
    SolarTerm("小暑", "YIN"),
    SolarTerm("大暑", "YIN"),
    SolarTerm("立秋", "YIN"),
    SolarTerm("处暑", "YIN"),
    SolarTerm("白露", "YIN"),
    SolarTerm("秋分", "YIN"),
    SolarTerm("寒露", "YIN"),
    SolarTerm("霜降", "YIN"),
    SolarTerm("立冬", "YIN"),
    SolarTerm("小雪", "YIN"),
    SolarTerm("大雪", "YIN"),
]