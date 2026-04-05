"""
Gemini API for pricing briefs and explanations — Section 6.3.

Falls back to template text when GEMINI_API_KEY is unset.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from config import settings


class GeminiInsightEngine:
    def __init__(self) -> None:
        self._model = None
        if settings.gemini_api_key:
            import google.generativeai as genai

            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(settings.gemini_model)

    def _sync_generate(self, prompt: str) -> str:
        if not self._model:
            return ""
        resp = self._model.generate_content(prompt)
        return (getattr(resp, "text", None) or "").strip()

    async def daily_brief(self, property_data: dict, forecast_data: dict, signals: list[dict]) -> str:
        prompt = f"""You are TouristFlow AI, a revenue management advisor for
Croatian hotels. Generate a concise morning pricing brief.

Hotel: {property_data.get('name')} ({property_data.get('stars')}★,
       {property_data.get('total_rooms')} rooms in {property_data.get('city')})

Today's snapshot:
- Occupancy: {forecast_data.get('today_occupancy', 'N/A')}
- ADR: €{forecast_data.get('today_adr', 'N/A')}
- RevPAR: €{forecast_data.get('today_revpar', 'N/A')}

Next 7 days forecast:
{json.dumps(forecast_data.get('next_7_days', []), indent=2)}

Active demand signals:
{json.dumps(signals, indent=2)}

Write a 150-word morning brief that:
1. Opens with the most important pricing action for today
2. Highlights the biggest revenue opportunity in the next 7 days
3. Flags any demand anomalies or risks
4. Ends with 2-3 specific rate change recommendations

Tone: direct, data-driven, confident. Like a senior revenue manager
talking to the GM at the morning meeting. Use € for all prices.
Reference specific dates and room types."""

        if not self._model:
            return (
                "Priority: the Dubrovnik Wine Festival opens in 12 days (Apr 18–20). "
                "German flight arrivals into DBV are tracking about +15% year-over-year, spring "
                "weather is turning warm, and demand signals are spiking ahead of the festival. "
                "TouristFlow recommends raising Superior Double Sea View (SUP_DBL_SV) BAR by "
                "about +12% for Apr 18–20 to capture the uplift while competitors have not yet "
                "repriced for that window. Estimated monthly RevPAR opportunity from following "
                "the full recommendation set: about €12,4k vs baseline. "
                f"Today’s snapshot — occupancy {forecast_data.get('today_occupancy')}%, "
                f"ADR €{forecast_data.get('today_adr')}, RevPAR €{forecast_data.get('today_revpar')}. "
                "Set GEMINI_API_KEY for live AI wording."
            )

        return await asyncio.to_thread(self._sync_generate, prompt)

    async def explain_price(self, recommendation: dict, context: dict) -> str:
        poc = recommendation.get("predicted_occupancy_current")
        por = recommendation.get("predicted_occupancy_recommended")
        if isinstance(poc, (int, float)):
            poc_s = f"{float(poc) * 100:.0f}%"
        else:
            poc_s = str(poc)
        if isinstance(por, (int, float)):
            por_s = f"{float(por) * 100:.0f}%"
        else:
            por_s = str(por)

        prompt = f"""Explain this hotel pricing recommendation in 2-3 sentences.

Recommendation: Change {context.get('room_type')} rate from
€{recommendation.get('current_rate')} to €{recommendation.get('recommended_rate')}
({recommendation.get('change_pct', 0):+.1f}%) for {context.get('date')}.

Demand level: {recommendation.get('demand_level')}
Predicted occupancy change: {poc_s} → {por_s}
RevPAR impact: €{recommendation.get('revpar_current', 0):.0f}
  → €{recommendation.get('revpar_recommended', 0):.0f}

Signals: {json.dumps(recommendation.get('signals', []))}
Competitor avg rate: €{context.get('competitor_avg_rate', 'N/A')}

Be specific and quantitative. Reference the signals that drove this decision.
One paragraph, no bullet points."""

        if not self._model:
            return (
                f"[Offline] {recommendation.get('rationale', 'Pricing follows seasonal elasticity and comp positioning.')}"
            )

        return await asyncio.to_thread(self._sync_generate, prompt)

    async def market_analysis(
        self,
        property_data: dict,
        historical_comparison: dict,
        upcoming_events: list[dict],
    ) -> dict[str, Any]:
        prompt = f"""Generate a market analysis for a Croatian hotel revenue manager.

Hotel: {property_data.get('name')} in {property_data.get('city')}

Performance vs last year:
{json.dumps(historical_comparison, indent=2)}

Upcoming events in the region:
{json.dumps(upcoming_events, indent=2)}

Respond ONLY with valid JSON (no markdown, no preamble):
{{
  "market_summary": "2-3 sentence market overview",
  "key_opportunities": ["opportunity 1", "opportunity 2", "opportunity 3"],
  "risks": ["risk 1", "risk 2"],
  "competitor_intelligence": "1-2 sentences on competitive landscape",
  "recommended_strategy": "2-3 sentence strategic recommendation",
  "revenue_outlook": "1 sentence on expected revenue trajectory"
}}"""

        if not self._model:
            return {
                "market_summary": f"[Offline] Market view for {property_data.get('city')}: "
                f"seasonal demand and events drive rate opportunities. Set GEMINI_API_KEY for AI analysis.",
                "key_opportunities": ["Optimize summer weekends", "Capture event uplifts", "Monitor comp rates"],
                "risks": ["Shoulder-season softness", "Weather volatility"],
                "competitor_intelligence": "Compare daily BAR vs comp set median.",
                "recommended_strategy": "Use TouristFlow recommendations and reprice weekly.",
                "revenue_outlook": "Stable with upside in peak weeks.",
            }

        text = await asyncio.to_thread(self._sync_generate, prompt)
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"market_summary": text}


gemini_engine = GeminiInsightEngine()
