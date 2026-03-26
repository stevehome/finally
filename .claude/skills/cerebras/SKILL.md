---
name: cerebras-inference
description: Use this to write code to call an LLM using LiteLLM with the Cerebras inference provider (direct, via api.cerebras.ai)
---

# Calling an LLM via Cerebras

These instructions allow you to write code to call an LLM with Cerebras as the inference provider.
This method uses LiteLLM directly against `api.cerebras.ai` — not via OpenRouter.

## Setup

The `CEREBRAS_API_KEY` must be set in the `.env` file and loaded as an environment variable.

The uv project must include litellm and pydantic.
`uv add litellm pydantic`

## Code snippets

Use code like these examples in order to use Cerebras.

### Imports and constants

```python
from litellm import completion
MODEL = "cerebras/qwen-3-235b-a22b-instruct-2507"
```

### Code to call via Cerebras for a text response

```python
response = completion(model=MODEL, messages=messages)
result = response.choices[0].message.content
```

### Code to call via Cerebras for a Structured Outputs response

```python
response = completion(model=MODEL, messages=messages, response_format=MyBaseModelSubclass)
result = response.choices[0].message.content
result_as_object = MyBaseModelSubclass.model_validate_json(result)
```
