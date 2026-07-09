# PEPM Metric

## Definition
PEPM (AI Spend Per Employee) is a metric developed in the [[ramp-revelio-2026-ai-jobs-impact-study]] to measure the intensity of AI adoption at the firm level. It calculates monthly AI vendor spend per employee over the first three months after sustained AI adoption begins.

## Formula
PEPM = (Σ²ₘ₌₀ AIᵢ,ɢᵢ₊ₘ) / (3 × HCᵢ,ɢᵢ₋₁)

Where:
- AIᵢ,ɢᵢ₊ₘ = AI vendor spend for firm i in month m after adoption
- HCᵢ,ɢᵢ₋₁ = baseline headcount in the month before adoption

## Methodology
1. AI adoption is defined as the first month of a three-consecutive-month spell where AI spend is at least $100 monthly
2. PEPM is calculated using AI spend over the first three months after adoption begins
3. Baseline headcount is measured in the month before adoption
4. Firms are sorted into intensity groups:
   - High intensity: top PEPM tercile
   - Low intensity: bottom two PEPM terciles

## Significance
- Provides a direct, observed measure of AI adoption intensity rather than relying on occupational exposure scores
- Allows researchers to distinguish between firms that adopt AI lightly versus intensively
- Correlates closely with adoption of more complex AI products and tools (coding agents, APIs) versus simpler chat subscriptions
- Enables analysis of differential impacts based on adoption intensity

## Key Findings Using PEPM
- High-intensity adopters (top tercile) grew employment by 10.2% following adoption
- Entry-level headcount rose 12.0% for high-intensity adopters
- Low-intensity adopters showed no statistically significant change in employment
- Gains emerged gradually, suggesting a "learning curve" as firms integrated AI tools

## Related Concepts
- [[ai-spend-per-employee-methodology]]
- [[ai-adoption-intensity-terciles]]
- [[high-intensity-ai-adopters]]
- [[low-intensity-ai-adopters]]

## Related Studies
- [[ramp-revelio-2026-ai-jobs-impact-study]]

## References
Kharazian, A., Simon, L., & Stevens, R. (2026). A New Look at AI's Impact on Jobs: Firm-Level AI Spending and Workforce Adjustment. Ramp and Revelio Labs.