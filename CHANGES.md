                    ┌─────────────────────┐
                    │      User           │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │      Gemma 4        │
                    │   Agent / Reasoner  │
                    └──────────┬──────────┘
                               │
                    Function calls / tools
                               │
          ┌────────────────────┼────────────────────┐
          ↓                    ↓                    ↓
   Mandi API Tool       Location Tool       Calculation Tools
          │                    │                    │
          ↓                    ↓                    ↓
   data.gov.in          Coordinates        Distance/Transport
          │                                         │
          └──────────────────┬──────────────────────┘
                             ↓
                    Market comparison
                             ↓
                         Gemma 4
                             ↓
                    Farmer explanation