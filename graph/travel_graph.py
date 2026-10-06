from langgraph.graph import StateGraph, START, END

from graph.state import TravelState
from agents.nodes import (
    query_analyzer,
    research_node,
    itinerary_generator,
    itinerary_critic,
    replanner,
)


def build_graph():
    builder = StateGraph(TravelState)

    builder.add_node("query_analyzer", query_analyzer)
    builder.add_node("web_research", research_node)
    builder.add_node("itinerary_generator", itinerary_generator)
    builder.add_node("critic", itinerary_critic)
    builder.add_node("replanner", replanner)

    builder.add_edge(START, "query_analyzer")
    builder.add_edge("query_analyzer", "web_research")
    builder.add_edge("web_research", "itinerary_generator")
    builder.add_edge("itinerary_generator", "critic")

    builder.add_conditional_edges(
        "critic",
        lambda state: (
            "replan"
            if state.get("critic_decision") == "REPLAN"
            else "end"
        ),
        {
            "replan": "replanner",
            "end": END,
        },
    )

    builder.add_edge("replanner", "critic")

    return builder.compile()


graph = build_graph()


def run_travel_planner(user_query: str):
    return graph.invoke({
        "user_query": user_query,
        "replan_attempts": 0,
    })
