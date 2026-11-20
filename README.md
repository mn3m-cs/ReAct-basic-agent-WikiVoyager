# ReAct-basic-agent-WikiVoyager

A small ReAct agent in Python, built on Simon Willison's example. The model thinks, picks an action, reads the result, and goes again until it has an answer. It looks things up on Wikipedia and arXiv instead of answering from memory, and the name comes from that: it moves from page to page to find the answer.

![ReAct diagram](https://react-lm.github.io/files/diagram.png)

![HotpotQA](https://react-lm.github.io/files/hotpotqa.png)

![ALFWorld](https://react-lm.github.io/files/alfworld.png)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env`:

- `XAI_API_KEY`: your xAI key
- `MODEL`: `xai:grok-4.20-0309-non-reasoning` by default
- `USER_AGENT`: Wikipedia blocks requests without a URL or email in it

## Run

```bash
python agent.py
```

Asks the default question: "What does England share borders with?"

```bash
python agent.py "Who wrote the ReAct paper?"
```

Actions: `wikipedia_search`, `wikipedia_page`, `arxiv_search`, `calculate`.

`calculate` uses `eval`, so it runs any Python the model writes. Don't run it on questions you don't trust.

## References

- https://react-lm.github.io/
- https://til.simonwillison.net/llms/python-react-pattern
