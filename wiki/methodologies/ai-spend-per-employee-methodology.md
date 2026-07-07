## AI Spend Per Employee Methodology

**First Observed:** 2026-07-03
**Last Updated:** 2026-07-03

### Definition
A direct measurement approach for quantifying firm-level AI adoption intensity by calculating monthly AI vendor spend per employee over the first three months after adoption begins. Developed by Ramp economists for the 2026 AI Jobs Impact Study, this methodology addresses limitations of occupational exposure scores and survey-based adoption measures.

### Calculation
PEPM_i = (Σ from m=0 to 2 of AI_{i,G_i+m}) / (3 × HC_{i,G_i-1})

Where:
- AI_{it} = monthly AI vendor spend
- G_i = first month of sustained AI adoption
- HC_{i,G_i-1} = baseline headcount in month before adoption

### Implementation Steps
1. **Adoption Definition**: First month of earliest three-consecutive-month spell with ≥$100 AI spend monthly
2. **Intensity Measurement**: Calculate PEPM using first three post-adoption months
3. **Group Classification**: Low intensity = bottom two PEPM terciles, High intensity = top tercile
4. **Comparison Design**: Compare earlier adopters to later adopters in same intensity group

### Advantages Over Alternative Methods
| Method | Limitations | PEPM Advantages |
|--------|-------------|-----------------|
| Occupational exposure scores | Vary only across occupations, not firms | Measures actual firm adoption decisions |
| Executive surveys | Capture awareness not implementation | Tracks payment data showing actual usage |
| AI-related job postings | Proxy for interest not adoption | Measures direct financial commitment |
| Resume AI skills | Lagging indicator of adoption | Captures immediate spending behavior |

### Key Insights from Application
- High-intensity adopters (PEPM top tercile) grew headcount by 10.2% over 24 months
- Low-intensity adopters showed no statistically significant employment changes
- Adoption intensity correlates with use of complex AI tools (coding agents, APIs)
- First three months of spending strongly predicts long-term adoption patterns

### Sectoral Variation
PEPM reveals significant sector differences in adoption intensity:
- Information sector firms show highest intensity adoption
- Professional services demonstrate moderate intensity
- Traditional sectors show minimal intensity despite some adoption

### Implications for Market Research
This methodology provides market researchers with:
1. A concrete way to measure client AI adoption beyond self-reported surveys
2. Evidence that AI investment intensity predicts organizational growth
3. Framework for segmenting clients by true AI integration maturity
4. Validation that direct spending data outperforms proxy measures

### Related Research
- The Ramp-Revelio 2026 study applied this methodology to 21,559 firms (see [[ramp-revelio-2026-ai-jobs-impact-study]])
- Contrasts with PwC's [[pwc-ai-occupational-exposure-index]] which uses task-based exposure scoring
- Addresses limitations documented in Burning Glass Institute's "Beyond the Binary"

### Update
2026-07-03: Added detailed calculation formula, implementation steps, and comparative advantages based on Ramp-Revelio 2026 study findings. Integrated sectoral variation analysis and market research implications.