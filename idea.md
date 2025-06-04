I want to build a LLM caching proxy server that emulates popular LLMs with the ability to simulate failures. We will call this Rubberduck.

## Features

- Caching: Since this proxy server will be used to test systems that use LLMs, it should be able to cache responses from the LLMs to avoid making unnecessary requests.
- LLM Emulation: The proxy server should be able to emulate popular LLMs from various, popular LLM providers. We will start with OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Google Vertex AI to start with.
- Failure Simulation: The proxy server should be able to simulate failures to test the robustness of the systems that use LLMs.
- Rate Limiting: The proxy server should be able to limit the number of requests per minute to avoid being rate limited by the LLMs.
- Authentication: It should be able to authenticate requests to the LLMs using the LLM keys provided in the API requests that come in. As for the proxy server itself, it will provide a flexible way for users to login / register.
- UI: The user journey looke something like this: 

    1. User logs in with their email and password or via social login (Google, GitHub, etc).
    2. User can create a new LLM proxy, which will have a name, description, LLM provider and LLM model. This creates a new LLM proxy running on a separate thread, binding to a separate port. On this port, the LLM proxy will act as a reverse proxy to the LLM API.
    3. The user needs to pass the LLM key in the API request to the LLM proxy. The LLM proxy will then authenticate the request to the LLM API and forward the request to the LLM API.
    4. Users will be able to configure the LLM proxy to simulate failures on a per LLM proxy basis, 
      - timeouts 
      - error injection
      - IP allow-list / block-list
      - rate limiting
    5. The LLM proxy will then cache the response from the LLM API and return the response to the user.
    6. The user can then use the LLM proxy in their system by pointing their system to the LLM proxy's URL.

- Rubberduck Settings:
  - Allow / disallow new user registration.
  - Allow / disallow login via social login (Google, GitHub, etc).
  - Allow / disallow login via email and password.
  - Global IP allow-list / block-list.
- Logging:
  - All requests to the LLM proxy should be logged.
  - All responses from the LLM proxy should be logged.
  - All errors from the LLM proxy should be logged.
  - Logs should indicate cache hits / misses.
  - Logs should indicate rate limit hits / misses.
  - Logs should indicate IP allow-list / block-list hits / misses.
  - Logs should indicate LLM cost, where available.

## Implementation

- The proxy server will be implemented in Python + FastAPI.
- The UI will be implemented using React + Shadcn UI.
- The database will be implemented using SQLite.
- Each LLM provider will have its own, modular implementation.
- Rubberduck authentication:
  - We will use FastAPI-Users for authentication.
  - An environment variable should control if Rubberduck should allow new user registration or not. If not, then only users with email addresses or domains should be able to register. This should be the default behavior.
  - The login page should allow users to login with their email and password, or via social login (Google, GitHub, etc).
