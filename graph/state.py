from typing import TypedDict, List, Dict, Any


class TravelState(TypedDict, total=False):
    user_query: str
    origin: str
    destination: str
    duration_days: int
    travelers: int
    budget: float
    currency: str
    interests: List[str]

    search_results: List[Dict[str, Any]]
    origin_location: Dict[str, Any]
    destination_location: Dict[str, Any]
    weather: Dict[str, Any]
    wikipedia: Dict[str, Any]
    route: Dict[str, Any]
    exchange_rate: Dict[str, Any]
    phase2_research: Dict[str, Any]

    itinerary: str

    critic_feedback: str
    critic_decision: str
    critic_report: str
    replan_attempts: int
