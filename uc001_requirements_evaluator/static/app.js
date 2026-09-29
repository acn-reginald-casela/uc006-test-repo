const form = document.getElementById("story-form");
const submitBtn = document.getElementById("submit-btn");

const statusCard = document.getElementById("status-card");
const loadingEl = document.getElementById("loading");
const errorEl = document.getElementById("error");

const resultCard = document.getElementById("result-card");
const resultStoryId = document.getElementById("result-story-id");
const resultFinalRequirement = document.getElementById("result-final-requirement");

const tokPrompt = document.getElementById("tok-prompt");
const tokCandidates = document.getElementById("tok-candidates");
const tokThoughts = document.getElementById("tok-thoughts");
const tokTotal = document.getElementById("tok-total");
const agentTableBody = document.getElementById("agent-table-body");

function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  loadingEl.hidden = !isLoading;
  if (isLoading) {
    statusCard.hidden = false;
    errorEl.hidden = true;
  }
}

function showError(message) {
  statusCard.hidden = false;
  loadingEl.hidden = true;
  errorEl.hidden = false;
  errorEl.textContent = message;
}

function renderResult(data) {
  resultCard.hidden = false;
  resultStoryId.textContent = data.story_id ?? "";
  resultFinalRequirement.textContent = data.final_requirement ?? "";

  const usage = data.token_usage ?? {};
  tokPrompt.textContent = usage.prompt_tokens ?? 0;
  tokCandidates.textContent = usage.candidates_tokens ?? 0;
  tokThoughts.textContent = usage.thoughts_tokens ?? 0;
  tokTotal.textContent = usage.total_tokens ?? 0;

  agentTableBody.innerHTML = "";
  const byAgent = usage.by_agent ?? {};
  const agentNames = Object.keys(byAgent);
  if (agentNames.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = '<td colspan="2">No per-agent data.</td>';
    agentTableBody.appendChild(row);
  } else {
    for (const agent of agentNames) {
      const row = document.createElement("tr");
      const nameCell = document.createElement("td");
      nameCell.textContent = agent;
      const tokensCell = document.createElement("td");
      tokensCell.textContent = byAgent[agent];
      row.append(nameCell, tokensCell);
      agentTableBody.appendChild(row);
    }
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const storyId = document.getElementById("story-id").value.trim();
  const sessionId = document.getElementById("session-id").value.trim();
  const requirements = document.getElementById("requirements").value.trim();

  resultCard.hidden = true;
  setLoading(true);

  try {
    const response = await fetch("/test-cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        story: { id: storyId, requirements: requirements || null },
        session_id: sessionId,
      }),
    });

    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json")
      ? await response.json()
      : await response.text();

    if (!response.ok) {
      const message =
        typeof payload === "string" ? payload : payload.error || JSON.stringify(payload);
      throw new Error(`Request failed (${response.status}): ${message}`);
    }

    statusCard.hidden = true;
    renderResult(payload);
  } catch (err) {
    showError(err.message || String(err));
  } finally {
    setLoading(false);
  }
});
