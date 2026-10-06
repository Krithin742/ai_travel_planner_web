from graph.state import TravelState
from agents.llm import get_llm, extract_json
from tools.research import specialized_research, format_research


def query_analyzer(state: TravelState) -> TravelState:
    prompt = f"""
You are a travel request parser.

Extract the travel information from this user request.

USER REQUEST:
{state["user_query"]}

Return ONLY valid JSON:
{{
  "origin": "city",
  "destination": "city",
  "duration_days": 4,
  "travelers": 2,
  "budget": 80000,
  "currency": "INR",
  "interests": ["shopping", "food", "sightseeing"]
}}

Rules:
- duration_days, travelers and budget must be numbers.
- interests must be a JSON list.
- If something is missing, make a reasonable explicit assumption.
"""
    data = extract_json(get_llm().invoke(prompt))
    return {**state, **data}


def research_node(state: TravelState) -> TravelState:
    return specialized_research(state)


def itinerary_generator(state: TravelState) -> TravelState:
    research = format_research(state)

    prompt = f"""
You are a professional travel itinerary generator.

USER REQUEST:
{state["user_query"]}

STRUCTURED TRIP:
Origin: {state["origin"]}
Destination: {state["destination"]}
Duration: {state["duration_days"]} days
Travelers: {state["travelers"]}
Budget: {state["budget"]} {state["currency"]}
Interests: {", ".join(state.get("interests", []))}

TOOL RESEARCH:
{research}

RULES:
1. Use the research as evidence.
2. Do not invent live weather, prices, exchange rates or opening hours.
3. Clearly mark estimates.
4. If a tool failed, do not fabricate a value.
5. Keep the plan within the stated budget where possible.
6. Give exactly the requested number of days.
7. Include weather and transport notes.
8. Mention the indicative exchange rate.
9. Keep source links when available.

OUTPUT:
Trip Overview
Weather Summary
Currency and Budget Notes
Transport and Route Notes
Day-by-day Itinerary
Food and Hotel Suggestions
Practical Travel Tips
Sources

Return only the final travel plan.
"""
    return {
        **state,
        "itinerary": get_llm().invoke(prompt),
    }


MAX_REPLAN_ATTEMPTS = 2


def itinerary_critic(state: TravelState) -> TravelState:
    research = format_research(state)

    prompt = f"""
You are a careful travel itinerary reviewer.

USER REQUEST:
{state.get("user_query", "")}

TRIP:
Origin: {state.get("origin")}
Destination: {state.get("destination")}
Duration: {state.get("duration_days")} days
Travelers: {state.get("travelers")}
Budget: {state.get("budget")} {state.get("currency")}
Interests: {state.get("interests")}

RESEARCH:
{research}

CURRENT ITINERARY:
{state.get("itinerary", "")}

Check:
1. Correct destination and duration.
2. Budget is discussed and unsupported exact prices are avoided.
3. Weather and transport claims match research.
4. No invented live facts.
5. Plan is coherent, practical and aligned with interests.

Return ONLY valid JSON:
{{"decision":"PASS" or "REPLAN","feedback":"Concise actionable review."}}
"""
    try:
        review = extract_json(get_llm().invoke(prompt))
        decision = str(review.get("decision", "REPLAN")).upper()
        feedback = str(review.get("feedback", "No feedback."))
        if decision not in {"PASS", "REPLAN"}:
            decision = "REPLAN"
    except Exception as exc:
        decision = "REPLAN"
        feedback = f"Critic parsing failed: {exc}"

    attempts = state.get("replan_attempts", 0)
    if decision == "REPLAN" and attempts >= MAX_REPLAN_ATTEMPTS:
        decision = "PASS"
        feedback += " Maximum replanning attempts reached."

    return {
        **state,
        "critic_decision": decision,
        "critic_feedback": feedback,
        "critic_report": feedback,
    }


def replanner(state: TravelState) -> TravelState:
    attempts = state.get("replan_attempts", 0) + 1

    prompt = f"""
Revise the travel itinerary using the critic feedback.

USER REQUEST:
{state.get("user_query", "")}

TRIP REQUIREMENTS:
Origin: {state.get("origin")}
Destination: {state.get("destination")}
Duration: {state.get("duration_days")} days
Travelers: {state.get("travelers")}
Budget: {state.get("budget")} {state.get("currency")}
Interests: {state.get("interests")}

RESEARCH:
{format_research(state)}

CRITIC FEEDBACK:
{state.get("critic_feedback", "")}

CURRENT ITINERARY:
{state.get("itinerary", "")}

Return the complete revised itinerary.
Do not invent live prices, opening hours, bookings, weather or transport facts.
Preserve the exact destination and number of days.
"""
    return {
        **state,
        "itinerary": get_llm().invoke(prompt),
        "replan_attempts": attempts,
    }
