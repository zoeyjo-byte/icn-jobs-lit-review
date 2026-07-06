# AI Spend Per Employee Methodology

The AI Spend Per Employee (PEPM) methodology is a measure of AI adoption intensity developed for the [[ramp-revelio-2026-ai-jobs-impact-study]]. This approach provides a direct, firm-level measure of AI investment that overcomes limitations of previous occupational exposure metrics.

## Definition

For a firm i, AI spend per employee is calculated as:

PEPM_i = (Σ_{m=0}^2 AI_{i,G_i+m}) / (3 × HC_{i,G_i-1})

Where:
- AI_{i,G_i+m} is monthly AI vendor spend in months 0-2 after adoption
- HC_{i,G_i-1} is baseline headcount in the month before adoption
- G_i is the first month of sustained AI adoption

Sustained AI adoption is defined as the first month of the earliest three-consecutive-month spell where AI spend is at least $100 per month.

## Implementation

1. **Adoption Timing**: Identify G_i as the first month where a firm spends at least $100 on AI vendors for three consecutive months
2. **Intensity Measurement**: Calculate PEPM using the first three months of AI spending after adoption
3. **Intensity Grouping**: Classify firms into low (bottom two terciles) and high (top tercile) intensity groups
   - High intensity: ~$33.67 per employee per month
   - Low intensity: ~$2.78 per employee per month

## Advantages Over Previous Methods

This methodology addresses key limitations of earlier approaches:
- **Direct measurement**: Observes actual AI spending rather than predicted exposure
- **Firm-level variation**: Captures differences between firms with identical workforce composition
- **Timing precision**: Identifies when adoption occurs rather than relying on proxies
- **Intensity differentiation**: Distinguishes between light and heavy AI users

## Key Findings Using This Methodology

The Ramp-Revelio study using this methodology found:
- High-intensity adopters grew headcount by 10.2% over 24 months
- Entry-level headcount rose 12.0% among high-intensity adopters
- Low-intensity adopters showed no statistically significant employment changes
- Gains were concentrated in the Information sector (13.4% growth)

## Relevance to Market Research

For market research professionals, this methodology provides a concrete way to measure AI adoption that can be applied to client organizations. It offers a more precise alternative to survey-based approaches and occupational exposure scores, enabling more accurate assessment of how AI investment correlates with business outcomes.

See also: [[ramp-revelio-2026-ai-jobs-impact-study]], [[ramp]], [[revelio-labs]]