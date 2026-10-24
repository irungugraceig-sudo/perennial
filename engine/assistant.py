"""Perennial's guided assistant.

Answers user questions about the calculator using the REAL engine numbers as
context, so it never contradicts the math on screen.

Two modes, chosen automatically:
  * Claude (Anthropic) when ANTHROPIC_API_KEY is set.
  * A scripted, rule-based guide otherwise (no key, no network) so the demo
    always works and deploys with no secrets.

The system prompt pins the assistant to Perennial's facts and honesty rules.
"""

from __future__ import annotations

import os

SYSTEM_PROMPT = (
    "You are the Perennial assistant, an expert guide inside the Perennial app. "
    "Perennial turns a city's discarded snow into clean cooling for GPU data centers using a "
    "sealed shell-and-tube heat exchanger, and quantifies the fresh water, chiller energy, and "
    "CO2 it saves. You can SEE the user's current scenario (facility, date, snowfall, efficiency, "
    "etc.) and the live results in the context. You can CHANGE inputs by calling the set_inputs "
    "tool, e.g. to try a snowier date, a different facility, or a higher collection efficiency. "
    "When the user asks a what-if ('what if we doubled collection?', 'try the Lowell site', "
    "'use the 2015 blizzard'), call set_inputs with the right fields, then explain what changed. "
    "Rules: snow cooling is SEASONAL and shaves the summer peak; never claim it replaces all "
    "cooling. Ground every number in the context; never invent figures. Be concise and friendly."
)

# Tool Claude can call to drive the calculator.
SET_INPUTS_TOOL = {
    "name": "set_inputs",
    "description": "Change one or more calculator inputs to run a what-if scenario.",
    "input_schema": {
        "type": "object",
        "properties": {
            "facility": {"type": "string", "description": "Data center name to select."},
            "date": {"type": "string", "description": "A date YYYY-MM-DD; drives snowfall used."},
            "collection_efficiency": {"type": "number", "description": "0-1 fraction of snow hauled."},
            "storms_per_season": {"type": "number"},
            "passive_loss_fraction": {"type": "number", "description": "0-1 pile melt loss."},
            "hx_effectiveness": {"type": "number", "description": "0-1 heat-exchanger effectiveness."},
            "chiller_cop": {"type": "number"},
            "credit_price_usd": {"type": "number"},
        },
    },
}


def _scripted_reply(message: str, context: dict | None) -> str:
    m = message.lower().strip()
    ctx = context or {}

    def num(key, default="—"):
        v = ctx.get(key)
        return f"{v:,.0f}" if isinstance(v, (int, float)) else default

    if any(w in m for w in ("hello", "hi", "hey", "start", "help")):
        return (
            "Hi! I'm your Perennial guide. Tell me about your data center and I'll show what "
            "snow cooling saves. Try: pick a facility, then ask 'how much water do I save?' or "
            "'what are carbon credits?'"
        )
    if "water" in m:
        return (
            f"With your current inputs, snow cooling saves about {num('fresh_water_saved_gallons')} "
            "gallons of fresh water a year, water a conventional cooling tower would evaporate. "
            "It works by dumping the data center's heat into melting snow instead of boiling off water."
        )
    if "carbon" in m or "credit" in m or "co2" in m:
        return (
            f"You avoid roughly {num('co2_avoided_tonnes')} tonnes of CO2 a year by displacing "
            "chiller electricity with free snow cooling. Each tonne is one carbon credit you can "
            "sell on voluntary markets, shown with a dollar value in the Footprint & Carbon tab."
        )
    if "peak" in m or "summer" in m:
        return (
            "Snow cooling shaves the SUMMER peak, the hottest weeks when cooling towers drink the "
            "most water and the grid is most stressed. You collect cold in winter and spend it in "
            "summer. Watch the month slider on the Savings tab."
        )
    if "how" in m and ("work" in m or "it" in m):
        return (
            "A shell-and-tube heat exchanger: your ultrapure coolant runs in sealed tubes, dirty "
            "snow meltwater flows around them in the shell. Heat crosses the metal, the two never "
            "mix, so filthy plowed snow can safely cool a data center. See the Logic tab diagram."
        )
    if "snow" in m or "collect" in m:
        return (
            "We estimate collected snow from NOAA snowfall times the plowed street area times a "
            "collection-efficiency factor, then cross-check against Boston's real ~89,000 cubic "
            "yards hauled per storm. Adjust the sliders to see how it changes the savings."
        )
    return (
        "I can explain water savings, carbon credits, the summer-peak idea, or how the heat "
        "exchanger works. Which would you like? (Tip: set a key for the full AI assistant.)"
    )


def _claude_reply(message: str, context: dict | None, history: list | None) -> dict:
    import anthropic  # lazy: only needed when a key is configured

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    ctx_text = "\n".join(f"{k}: {v}" for k, v in (context or {}).items())

    messages = []
    for turn in (history or [])[-6:]:
        role = "user" if turn.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": turn.get("content", "")})
    messages.append({"role": "user", "content": f"Current scenario + live results:\n{ctx_text}\n\nUser: {message}"})

    resp = client.messages.create(
        model=model, max_tokens=500, system=SYSTEM_PROMPT,
        tools=[SET_INPUTS_TOOL], messages=messages,
    )

    set_inputs: dict = {}
    for block in resp.content:
        if getattr(block, "type", "") == "tool_use" and block.name == "set_inputs":
            set_inputs.update(block.input or {})

    # If Claude used a tool, send the result back so it can phrase a final answer.
    if set_inputs:
        messages.append({"role": "assistant", "content": resp.content})
        tool_use_id = next(
            (b.id for b in resp.content if getattr(b, "type", "") == "tool_use"), None
        )
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": "Applied: " + ", ".join(f"{k}={v}" for k, v in set_inputs.items()),
            }],
        })
        resp = client.messages.create(
            model=model, max_tokens=500, system=SYSTEM_PROMPT,
            tools=[SET_INPUTS_TOOL], messages=messages,
        )

    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return {"reply": text, "set_inputs": set_inputs}


def assistant_reply(message: str, context: dict | None = None, history: list | None = None) -> dict:
    """Return {'reply': str, 'mode': 'claude'|'scripted', 'set_inputs': dict}."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            r = _claude_reply(message, context, history)
            return {"reply": r["reply"], "mode": "claude", "set_inputs": r["set_inputs"]}
        except Exception:
            pass  # fall back gracefully on any error
    return {"reply": _scripted_reply(message, context), "mode": "scripted", "set_inputs": {}}
