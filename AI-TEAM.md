# AI Employee Team

Eight Claude Code subagents live in `.claude/agents/`.

| Agent | Domain |
|---|---|
| chief-of-staff | Leads the team. Routes work. Merges results. |
| social-media-manager | Social media |
| talent-recruiter | Hiring |
| tech-lead | Technical |
| research-analyst | Research papers |
| operations-manager | Operations |
| automation-engineer | Building automations |
| partnerships-lead | Leads and partners |

## Use

- Start with the lead: `Use chief-of-staff to launch our Q1 campaign`
- Call one agent: `Use research-analyst to summarize 5 recent papers on RAG`

## Rules for all agents

- Drafts only. A human approves any post, email, offer, payment, or contract.
- Cite sources. Verify links.
- Keep secrets out of the repo.

## Connectors worth adding

Zapier, Google Drive, Canva, Ahrefs, Vibe Prospecting, PubMed, and Render are already linked to this session. Authorize HubSpot and Make for the leads and automation agents.
