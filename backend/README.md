# Backend

FastAPI backend for the AI Operating System Assistant.

The backend owns the safety pipeline:

```text
structured intent -> validation -> preview -> confirmation -> safe execution -> logging
```

Routes should stay thin. Business logic belongs in services, validation belongs in validators, and filesystem behavior belongs in tools.
