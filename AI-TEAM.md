# AI Employee Team

Fourteen Claude Code subagents live in `.claude/agents/`.

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
| task-coordinator | Daily updates, assign and review candidate tasks |
| youtube-channel-manager | 3 to 4 YouTube channels |
| sales-executive | Sales |
| accounts-manager | Accounts |
| whatsapp-candidate-liaison | WhatsApp to candidates |
| lead-desk | Lead queries and responses |

## Use

- Start with the lead: `Use chief-of-staff to launch our Q1 campaign`
- Call one agent: `Use research-analyst to summarize 5 recent papers on RAG`

## Rules for all agents

- Drafts only. A human approves any post, email, offer, payment, or contract.
- Cite sources. Verify links.
- Keep secrets out of the repo.

## WhatsApp setup

No agent has a live WhatsApp link yet. Pick one:
- WhatsApp Business Cloud API (Meta) with a webhook.
- Zapier or Make with a WhatsApp Business app.

Until connected, agents write messages to `/outputs/whatsapp/` for a human to send.

## Connectors worth adding

Zapier, Google Drive, Canva, Ahrefs, Vibe Prospecting, PubMed, and Render are already linked to this session. Authorize HubSpot and Make for the leads and automation agents.
