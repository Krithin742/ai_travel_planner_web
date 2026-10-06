async function createPlan() {
    const query = document.getElementById("query").value.trim();
    const button = document.getElementById("planBtn");
    const status = document.getElementById("status");
    const result = document.getElementById("result");

    if (!query) {
        status.textContent = "Please describe your trip.";
        return;
    }

    button.disabled = true;
    status.textContent = "Agents are researching and reviewing your trip...";
    result.classList.add("hidden");

    try {
        const response = await fetch("/api/plan", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({user_query: query})
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Planning failed.");
        }

        document.getElementById("destination").textContent = data.destination || "-";
        document.getElementById("days").textContent = data.duration_days || "-";
        document.getElementById("budget").textContent =
            data.budget ? `${data.budget} ${data.currency || ""}` : "-";
        document.getElementById("critic").textContent = data.critic_decision || "-";
        document.getElementById("itinerary").textContent = data.itinerary || "";
        document.getElementById("feedback").textContent = data.critic_feedback || "No feedback.";
        document.getElementById("attempts").textContent = data.replan_attempts || 0;

        result.classList.remove("hidden");
        status.textContent = "Trip plan generated successfully.";
    } catch (error) {
        status.textContent = "Error: " + error.message;
    } finally {
        button.disabled = false;
    }
}
