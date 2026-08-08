# Signal Bridge External Beta Usability Review — 2026-08-07

Status: ACTIONED IN `feat/beta-clarity-trade-workflow-v1`

## Raw product problem discovered

A smart first-time viewer understood that Signal Bridge involved journaling, but could not immediately answer:

- Where are the charts, P&L, and visible trading information?
- Is this mainly a journal?
- If I see a trade idea on TikTok, Discord, or from another trader, what do I actually do with Signal Bridge?
- Do I log the trade before entry or after it?
- How do I upload/capture my trade and screenshot?
- Does one winning logged trade validate the trader/creator who gave the idea?
- How much of the product is AI-generated or black-box automation?

The visual shell was considered good, but the first-use mental model was not obvious enough.

## Product decisions from the review

### 1. Show trading before explaining infrastructure

The home page should immediately show genuine project chart imagery and historical research numbers. Real project artifacts are preferable to generic trading illustrations.

Historical results must retain their original sample/configuration labels. They are not live-performance claims and unlike tests are never blended.

### 2. Make the user workflow explicit

The first-use path is:

`trade idea -> capture thesis -> execute/pass -> attach chart + result/P&L/R -> review -> build a sample`

A user may journal after a completed trade in one step, or journal before the trade using `result=OPEN` and close the record later with `/journal-update`.

### 3. Preserve the original thesis

`/journal-update` changes result/P&L/R and adds a post-trade review without overwriting the original raw journal note. The pre-trade thought process remains available for later review.

### 4. Do not validate personalities

Signal Bridge does not validate a creator, influencer, mentor, or friend because one called trade wins. The unit of evaluation is the defined setup/rule/model over repeated observations.

Where an idea came from can be written in the immutable original note. Future structured provenance can normalize this later without changing the raw record.

### 5. Remove AI-product vibes from public positioning

Signal Bridge should present as trading software built around visible rules, charts, trades, P&L, screenshots, and evidence. Automation may route, store, schedule, and organize records behind the scenes, but public product copy should not market a black box or imply that generated text is the product.

## Implementation in this tranche

- trader-first home hero
- authentic archived MES chart in the first screen
- real historical research metrics with sample caveats
- dedicated charts + numbers section
- plain-English `What do I actually do?` workflow
- journal page `after the trade` and `before the trade` paths
- `/journal-update` command for user-owned records
- technical status moved behind a disclosure instead of leading the Journal page
- public clarity layer contains no AI / artificial-intelligence marketing language

## Evidence governance

This review changes presentation and workflow, not trading-edge status. No strategy component becomes validated because of this product pass.