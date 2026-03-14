"""Lightweight tech recommendation and scoring."""

from typing import Dict, List


TECH_CHARACTERISTICS = {
    "BPSK": {"best_scenarios": {"storm", "solar_flare", "long_distance"}, "weakness": {"time_critical"}},
    "QPSK": {"best_scenarios": {"balanced", "medium_distance"}, "weakness": {"storm"}},
    "16QAM": {"best_scenarios": {"clear", "short_distance", "high_bandwidth"}, "weakness": {"rain", "storm", "long_distance"}},
}


def get_tech_score(modulation: str, coding: str, scenario_conditions: Dict[str, object]) -> int:
    score = 100
    mod_char = TECH_CHARACTERISTICS.get(modulation, {"best_scenarios": set(), "weakness": set()})
    weather = str(scenario_conditions.get("weather", "clear"))
    snr = float(scenario_conditions.get("snr", 10))

    if weather in mod_char["weakness"]:
        score -= 20
    if weather in mod_char["best_scenarios"]:
        score += 15
    if snr < 5 and coding.startswith("Polar"):
        score += 20
    if snr > 15 and coding == "None":
        score += 10
    return max(0, min(130, score))


def recommend_tech_combo(level_config: Dict[str, object], weather: str) -> List[Dict[str, object]]:
    snr = float(level_config.get("snr_db", 10))
    if weather in {"storm", "solar_flare"} and snr < 5:
        return [{"modulation": "BPSK", "coding": "Polar(512,256)", "reason": "极端环境优先稳健性", "score": 95}]
    if weather == "clear" and snr > 12:
        return [{"modulation": "16QAM", "coding": "Hamming(7,4)", "reason": "晴朗高SNR优先吞吐", "score": 90}]
    return [{"modulation": "QPSK", "coding": "Polar(256,128)", "reason": "默认平衡方案", "score": 85}]
