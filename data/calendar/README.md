# Curated Catalyst Calendar

Events that matter and that no connected source publishes: a launch window, a
product launch, a regulatory decision date, an investor day. AIS reads this file
and reports what is in it. It never infers an event that is not here.

The file is `events.json` in this directory. The path can be moved with
`AIS_CATALYST_CALENDAR`.

## Schema

```json
{
  "events": [
    {
      "kind": "launch_window",
      "date": "2026-10-05",
      "description": "Neutron 火箭发射窗口",
      "symbol": "RKLB",
      "source": "Company guidance",
      "confirmed": false
    }
  ]
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `kind` | yes | One of the kinds below. Anything else is skipped with a warning. |
| `date` | yes | `YYYY-MM-DD`. A date that cannot be read is skipped, never guessed. |
| `description` | yes | What the event is, in the words a reader should see. |
| `symbol` | no | The asset it belongs to. Omit it for an event that bears on everything. |
| `source` | no | Where the date came from. Defaults to `Curated calendar`. |
| `confirmed` | no | `true` only when the date is settled. Anything else reads as unconfirmed. |

## Kinds

Which layer an event belongs to — company, industry or macro — is **not** written
here. AIS reads it from the kind, in `models/catalyst_event.py`, so that a
curator states what is happening and not how AIS should weigh it.

| Layer | Kinds |
| --- | --- |
| Company | `earnings`, `ex_dividend`, `dividend`, `split`, `investor_day`, `product_launch`, `launch_window`, `regulatory`, `shareholder_meeting` |
| Industry | `industry_policy`, `competition`, `industry_news` |
| Macro | `fomc`, `inflation`, `employment`, `growth`, `rates`, `fiscal_policy`, `tariff`, `currency` |

Adding a kind is a change to that enumeration and to the labels beside it. It is
not a change to the evaluator, which never names a kind.

## Rules for maintaining this file

- **Enter dates you can point at.** Put where it came from in `source`.
- **`confirmed: true` means settled.** A window that has not been announced is
  `false`, and the report says so.
- **Delete events once they pass.** They are filtered out either way, but a file
  full of old dates is a file nobody reads.
- **An empty file is fine.** It says no curated events have been entered, and the
  report says the industry layer has nothing on it.
