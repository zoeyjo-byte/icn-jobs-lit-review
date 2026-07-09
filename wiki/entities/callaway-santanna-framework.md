# Callaway-Sant'Anna Framework

## Definition
The Callaway-Sant'Anna framework is an econometric approach for analyzing treatment effects when units receive treatment at different times, as implemented in the [[ramp-revelio-2026-ai-jobs-impact-study]] to analyze the impact of AI adoption on employment.

## Methodology
- Developed by Callaway and Sant'Anna (2021) to address limitations of conventional two-way fixed effects event studies
- Designed for staggered adoption designs where firms begin treatment (AI adoption) at different points in time
- Estimates group-time average treatment effects separately for different adoption cohorts
- Compares earlier adopters to later adopters in the same intensity group while the later adopters have not yet adopted

## Implementation in Ramp-Revelio Study
- Used to estimate the relationship between firm-level AI adoption and employment
- Applied separately to low and high AI intensity adoption groups
- For high-intensity adopters, compared firms that adopted early to firms that would eventually be high-intensity adopters but hadn't yet adopted
- Included NAICS sector fixed effects to address selection into early AI adoption

## Advantages Over Traditional Methods
- Better suited to heterogeneous treatment timing than single two-way fixed effects event studies
- Reduces bias that can occur when treatment effects are heterogeneous across adoption cohorts
- Allows for more precise estimation of dynamic treatment effects
- Provides cleaner pre-treatment diagnostics for parallel trends assumption

## Key Findings Enabled by This Framework
- Revealed that high-intensity AI adopters grew employment by 10.2% following adoption
- Showed that these gains emerged gradually over 18-24 months
- Demonstrated that low-intensity adopters showed no statistically significant change in employment
- Provided evidence against predictions that AI adoption would lead to broad job losses

## Related Concepts
- [[staggered-treatment-timing]]
- [[causal-inference-in-ai-studies]]
- [[ai-adoption-selection-bias]]

## Related Studies
- [[ramp-revelio-2026-ai-jobs-impact-study]]

## References
Callaway, B., & Sant'Anna, P. H. (2021). Difference-in-Differences with Multiple Time Periods. Journal of Econometrics, 225(2), 200-230.

Kharazian, A., Simon, L., & Stevens, R. (2026). A New Look at AI's Impact on Jobs: Firm-Level AI Spending and Workforce Adjustment. Ramp and Revelio Labs.