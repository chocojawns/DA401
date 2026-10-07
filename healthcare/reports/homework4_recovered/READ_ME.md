# Coverage audit: why 32 was not the final answer

The earlier research panel is not directly comparable to the professor's kept
count because our implementation changed both denominator definitions and
eligibility rules. The assignment's worksheet permits dropping unresolvable
missing values; it does not specify our added positive/minimum-equity screen.
The user's current repository Homework 4 implementation requires all six years;
the later agreed research threshold is at least five. Neither should be silently
substituted for the other.

## Results from the saved SEC facts

|Definition|Companies|
|---|---:|
|Requested healthcare universe|59|
|Previous original-filing/average-balance analysis, at least 5 unflagged years|32|
|Homework method, at least 5 matched finite years|49|
|Homework method, all 6 consecutive years|47|
|Homework method, at least 5 unflagged equity years|43|
|Professor's worksheet benchmark|45|

**The data-completeness shortfall is substantially resolved.** We have not
exactly replicated the professor's unknown code and data snapshot. A kept-ticker
list and full method would be needed for an exact reconciliation. Do not drop
arbitrary firms to manufacture 45.

## What changed

The replay uses the existing Homework 4 selection functions: year-end balances,
later same-accession comparative figures, existing parent-income and equity
fallbacks (consolidated amounts minus explicitly reported noncontrolling
interests), and a September 23, 2026 filing cutoff. The research pipeline instead
requires original-filing metadata, beginning and ending balance availability,
and removes flagged equity rows. Thus recovered financial histories do not
imply every missing original Item 1A was recovered.

**This is a separate year-end-balance dataset, not a patch to the old ratios.**
Do not compare its medians with the earlier charts as though only sample size
changed. The whole sample has been recalculated consistently. It is appropriate
for retrospective description, not a point-in-time forecasting claim.

## Recovered comparison candidates

Eleven companies previously below five unflagged years now meet that threshold:
ABBV, A, CNC, CI, HUM, RMD, STE, TMO, UNH, UHS and ZBH.
This yields 43 firms. The included HealthcareAnalysis output was run on the new
homework_basis dataset and automatically applies the five-year/equity rules.

Six additional data-complete firms are retained in source files but excluded
from that conservative comparison: CAH, COR, DVA, HCA, MCK and MTD. Each has fewer
than five unflagged equity years. Negative or very small equity can make ROE
misleading; a negative ratio need not mean a net loss. They remain eligible for
separate accounting discussion and the assignment's raw completeness count.

Ten companies still have fewer than five matched years under this replay:
BIIB (4), BSX (4), EW (4), GEHC (4), IQV (4), JNJ (0), SOLV (3), SYK (0),
VTRS (0), WAT (3). These are extraction-method counts, not assertions that
no SEC statements exist. Differently tagged parent equity/income and short
public-company histories remain issues for targeted review.

## Validation and its limits

- Replayed all 59 tickers against locally cached Company Facts, with cache hashes.
- Matched income, revenue, assets and equity within the same accession and dates.
- Excluded nonfinite values and zero/invalid denominators; retained equity warnings.
- Checked six-year period continuity and DuPont arithmetic.
- Checked all 14 competing revenue selections for CNC, HUM, PODD and PFE against
  period-specific inline values in the cached statements. The selected values
  appear in total-revenue rows; quotations/links are in revenue_source_evidence.json.
- Tests cover year-end rather than average denominators, negative/zero equity,
  accession mismatches and filing cutoffs.

This is not a manual verification of every accounting value, nor does larger
coverage establish representativeness or causality. Centene total revenues
include premium taxes; peers' revenue scopes and pass-through amounts should be
explained when comparing margins/turnover. Current-company survivorship,
restatements, acquisitions and fiscal-calendar differences still matter.

No additional SEC downloads or paid AI calls were used. Original results remain
unchanged. Draft subsector classifications still need validation; the supplied
new analysis retains Unclassified labels rather than pretending that work is done.
