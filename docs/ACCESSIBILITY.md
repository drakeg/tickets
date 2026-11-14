# Text contrast verification

2026-11-14: user audit reported `color-contrast` on three nodes (selectors not
supplied). Reproduction on the live instance identified the shared Search button
and dashboard description; a broader route scan found repeated occurrences plus
an outlined-primary control. This is not an assertion that the original audit's
three individual nodes are known.

WCAG 2.2 SC 1.4.3 requires at least 4.5:1 for normal text:
https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html

| Palette | Before | After |
|---|---|---|
| Muted text on #f3f6fa | #61758a, 4.38:1 | #526579, 5.54:1 |
| Secondary outline text on #f3f6fa | Bootstrap #6c757d, 4.33:1 | #526579, 5.54:1 |
| Secondary hover/active | Bootstrap defaults | white on #526579, 6.01:1 |
| Primary outline text on #f3f6fa | Bootstrap defaults | #08746f, 5.18:1 |

Evidence: Chrome headless with axe-core color-contrast rule, real local Docker
instance. Checked signed-out dashboard/login; signed-in dashboard, tickets,
projects, knowledge-base, inventory, ticket/project/article creation; and a
390x844 signed-in dashboard. Before: 10 failing node occurrences across these
11 page/view checks. After: zero failing nodes in the same checks. Layout and
backend behavior are unchanged. All 91 Django tests pass, including a regression
that computes contrast for the shared muted palette and button colors.

Recheck with an accessibility browser extension's color-contrast rule after
palette changes, including hover/active states. For automated checking, inject
axe-core into the rendered page and run `axe.run(document, {runOnly:
['color-contrast']})`. Browser audit dependencies were temporary, not added to
application requirements. This verifies the checked rule/views, not full-site
WCAG conformance or every data-dependent content state.
