<style>
.cpoc-hero {
  padding: 2.5rem 0 2rem;
  text-align: center;
  border-bottom: 1px solid var(--md-default-fg-color--lightest);
  margin-bottom: 2rem;
}
.cpoc-hero h1 { font-size: 2.2rem; margin-bottom: 0.5rem; }
.cpoc-hero p {
  font-size: 1.1rem;
  color: var(--md-default-fg-color--light);
  max-width: 40rem;
  margin: 0 auto;
}
.cpoc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin: 2rem 0;
}
.cpoc-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--md-default-fg-color--lightest);
  border-radius: 0.5rem;
  padding: 1.5rem;
  background: var(--md-code-bg-color);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.cpoc-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12); }
.cpoc-card .cpoc-tag {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--md-primary-fg-color);
  background: rgba(0, 188, 235, 0.14);
  padding: 0.2rem 0.6rem;
  border-radius: 1rem;
  margin-bottom: 0.75rem;
  width: fit-content;
}
.cpoc-card h2 { margin: 0 0 0.5rem; font-size: 1.3rem; }
.cpoc-card p.cpoc-desc { color: var(--md-default-fg-color--light); flex-grow: 1; margin-bottom: 1rem; }
.cpoc-stats { display: flex; gap: 1.25rem; font-size: 0.8rem; color: var(--md-default-fg-color--light); margin-bottom: 1.25rem; }
.cpoc-stats strong { color: var(--md-default-fg-color); }
.cpoc-footer { text-align: center; color: var(--md-default-fg-color--light); font-size: 0.85rem; margin-top: 2.5rem; }
</style>

<div class="cpoc-cta" markdown>
<div class="cpoc-cta-logos">
<img src="assets/cisco-logo.png" alt="Cisco">
<img src="assets/cpoc-logo.png" alt="Customer Proof of Concept">
</div>

<div class="cpoc-hero" markdown>
# CPOC Lab Guides

Step-by-step Customer Proof of Concept lab guides. (TEMPLATE: replace this sentence.)
</div>

<div class="cpoc-grid" markdown>

<div class="cpoc-card" markdown>
<span class="cpoc-tag">Example</span>

## Example Guide

<p class="cpoc-desc">An example guide that shows the page structure. Create a new guide folder and run sync_scenarios.py to get a card like this one added for you.</p>

<div class="cpoc-stats"><span><strong>3</strong> scenarios</span></div>

<div class="cpoc-btn-row" markdown>
[Start the Example Guide →](example-guide/index.md){ .cpoc-btn }
[PDF](#){ .cpoc-btn .cpoc-btn--outline data-pdf-guide="example-guide" }
</div>
</div>

</div>

## Disclaimer

Test results are suitable to the specific design, configuration, test procedure, and types of switches deployed in the environment described in this document.

This document is provided "As-Is," without warranty of any kind, express or implied, including without limitation those of merchantability, fitness for a particular purpose, and non-infringement arising from a course of dealing, usage, or trade practice.

All printed copies and duplicate soft copies are not considered controlled; therefore, please refer to the original online version for the latest version.

<div class="cpoc-footer" markdown>
*CPOC — Your Name ([you@example.com](mailto:you@example.com))*
</div>

</div>
