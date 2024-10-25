# OpenAI Compatible API for Amazon Bedrock

This lambda provides an OpenAI compatible API for Amazon Bedrock. It uses the Amazon Bedrock API and libraries and exposes an API that is compatible with OpenAI's which is what most tools have standardised on now.

- [OpenAI Compatible API for Amazon Bedrock](#openai-compatible-api-for-amazon-bedrock)
  - [Building Locally](#building-locally)
  - [Diagrams](#diagrams)
  - [Future Improvements](#future-improvements)
    - [OptiLLM Integration](#optillm-integration)

It was originally based off of an official AWS Example then rewritten with a number of improvements:

- Asynchronous handling of requests.
- Support for newer models.
- Support for a fallback model when the primary model is not available.
- Improved error handling.
- Improved logging.
- Improved performance with larger requests.
- Improved prompting flexibility.
- **Currently in BETA**: Support for Optillm to perform optimisation of prompts and automated prompting techniques.

## Building Locally

You can build the Docker image locally and run it with the following command:

```bash
docker build -t bedrock-gateway .
docker run -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -p 9000:8080 -it bedrock-gateway

# Test the lambda invokes (won't submit a request to bedrock)
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d "{"""msg""":"""hello"""}"
```

## Diagrams

Component Diagram

```mermaid
graph TB
    Client[Client Applications]
    Gateway[Bedrock Access Gateway λ]
    Bedrock[Amazon Bedrock]
    Auth[Authentication Layer]

    subgraph Lambda["Bedrock Access Gateway λ"]
        FastAPI[FastAPI Application]
        Routers[API Routers]
        Models[Model Handlers]
        Schema[Data Schema]
    end

    Client -->|OpenAI Compat API Requests| Gateway
    Gateway -->|Authentication| Auth
    Gateway -->|Model Requests| Bedrock

    FastAPI --> Routers
    Routers --> Models
    Models --> Schema

    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:white;
    classDef lambda fill:#009900,stroke:#232F3E,stroke-width:2px,color:white;

    class Bedrock aws;
    class Gateway,Lambda lambda;
```

Sequence chart

```mermaid
sequenceDiagram
    participant C as Client
    participant G as Gateway API
    participant A as Auth
    participant M as Model Handler
    participant B as Bedrock

    C->>G: POST /api/v1/chat/completions
    G->>A: Validate API Key

    alt Invalid API Key
        A-->>G: 401 Unauthorized
        G-->>C: Authentication Error
    end

    G->>M: Process Chat Request
    M->>M: Validate Model & Parameters

    alt Invalid Model
        M-->>G: Use Fallback Model
    end

    M->>B: Invoke Bedrock Model

    alt Stream Response
        B-->>M: Stream Chunks
        loop For Each Chunk
            M-->>G: Process Chunk
            G-->>C: Send SSE Response
        end
    else Normal Response
        B-->>M: Complete Response
        M-->>G: Process Response
        G-->>C: Send JSON Response
    end
```

Class diagram

```mermaid
classDiagram
    class BaseChatModel {
        <<abstract>>
        +list_models() list
        +validate(chat_request)
        +chat(chat_request) ChatResponse
        +chat_stream(chat_request) AsyncIterable
    }

    class BedrockModel {
        -_supported_models dict
        +list_models() list
        +validate(chat_request)
        +chat(chat_request) ChatResponse
        +chat_stream(chat_request) AsyncIterable
        -_parse_request(chat_request) dict
        -_create_response(...) ChatResponse
    }

    class BaseEmbeddingsModel {
        <<abstract>>
        +embed(request) EmbeddingsResponse
    }

    class CohereEmbeddingsModel {
        +embed(request) EmbeddingsResponse
        -_parse_args(request) dict
    }

    class TitanEmbeddingsModel {
        +embed(request) EmbeddingsResponse
        -_parse_args(request) dict
    }

    BaseChatModel <|-- BedrockModel
    BaseEmbeddingsModel <|-- CohereEmbeddingsModel
    BaseEmbeddingsModel <|-- TitanEmbeddingsModel
```

Process flow

```mermaid
flowchart TD
    A[Client Request] --> B{Authenticate}
    B -->|Invalid| C[Return 401]
    B -->|Valid| D{Check Model}

    D -->|Supported| E[Validate Request]
    D -->|Unsupported| F[Use Fallback Model]
    F --> E

    E -->|Valid| G{Stream?}
    E -->|Invalid| H[Return 400]

    G -->|Yes| I[Setup Stream]
    G -->|No| J[Single Request]

    I --> K[Process Chunks]
    K --> L[Stream Response]

    J --> M[Process Response]
    M --> N[Return JSON]

    style A fill:#f9f,stroke:#333,stroke-width:4px
    style C fill:#f66,stroke:#333,stroke-width:2px
    style H fill:#f66,stroke:#333,stroke-width:2px
    style L fill:#6f6,stroke:#333,stroke-width:2px
    style N fill:#6f6,stroke:#333,stroke-width:2px
```

## Future Improvements

### OptiLLM Integration

Not yet implemented, but the plan is to integrate OptiLLM for optimisation of requests.

It might look something like:

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as Bedrock Gateway λ
    participant Optillm as Optillm Adapter
    participant Auth as Authentication Layer
    participant Model as Bedrock Model Handler
    participant Bedrock as Amazon Bedrock

    Note over Client,Bedrock: Flow when Optillm is enabled
    Client->>Gateway: POST /chat/completions
    Gateway->>Auth: Validate API Key
    Gateway->>Optillm: Optimise Request

    alt Optimisation Approach Selected
        Optillm->>Optillm: Apply Selected Strategy<br/>(moa/bon/mcts etc)
        Optillm-->>Gateway: Return Optimised Prompt
    else Direct Path
        Optillm-->>Gateway: Return Original Request
    end

    Gateway->>Model: Process Request
    Model->>Model: Validate Parameters
    Model->>Bedrock: Invoke Model API

    alt Stream Response
        loop For Each Chunk
            Bedrock-->>Model: Stream Chunks
            Model-->>Gateway: Process Chunk
            Gateway-->>Client: Send SSE Response
        end
    else Normal Response
        Bedrock-->>Model: Complete Response
        Model-->>Gateway: Process Response
        Gateway-->>Client: Send JSON Response
    end
```

```mermaid
classDiagram
    class BedockGatewayLambda {
        +process_request()
        +handle_stream()
        +handle_response()
    }

    class OptillmAdapter {
        -enabled: bool
        -approach: str
        -optimisers: dict
        +optimise_request()
        -import_optimisers()
    }

    class AuthenticationLayer {
        +validate_api_key()
    }

    class BedrockModelHandler {
        +validate()
        +chat()
        +chat_stream()
    }

    class Optimisers {
        +mcts()
        +bon()
        +moa()
        +rto()
        +other_approaches()
    }

    BedockGatewayLambda --> OptillmAdapter: Uses
    BedockGatewayLambda --> AuthenticationLayer: Uses
    BedockGatewayLambda --> BedrockModelHandler: Uses
    OptillmAdapter --> Optimisers: Imports when enabled
    BedrockModelHandler --> AmazonBedrock: Invokes

    note for OptillmAdapter "Conditionally loaded based on ENABLE_OPTILLM"
    note for Optimisers "Individual optimisers loaded as needed"
```

```mermaid
flowchart TB
    Start([Client Request]) --> Auth{Authentication<br/>Check}
    Auth -->|Invalid| Return401[Return 401]

    Auth -->|Valid| ParseReq[Parse Request & Extract<br/>Optimisation Settings]

    ParseReq --> CheckOpt{Check Optillm<br/>Configuration}

    %% Direct path without optimisation
    CheckOpt -->|Disabled| DirectPath[Direct to Bedrock]
    DirectPath --> ResponseType

    %% Optimisation path
    CheckOpt -->|Enabled| CheckApp{Check Approach<br/>In Model Name or<br/>Request Body}

    %% Technique Selection
    CheckApp -->|Combined| CombinedOps{Operation<br/>Type}
    CheckApp -->|Single| SingleTech{Single<br/>Technique}

    %% Combined Operations
    CombinedOps -->|AND Sequential| SeqProcess[Sequential Processing]
    CombinedOps -->|OR Parallel| ParProcess[Parallel Processing]

    %% Sequential Processing Detail
    SeqProcess --> SeqTechs["Process Techniques in Order
        1. First Technique
        2. Pass Result to Next
        3. Continue Chain"]

    %% Parallel Processing Detail
    ParProcess --> ParTechs["Process All Techniques
        • Run in Parallel
        • Collect All Results
        • Return as Array"]

    %% Individual Techniques
    SingleTech -->|Chain-of-Thought| CoT["CoT Reflection
        • Think
        • Reflect
        • Output"]

    SingleTech -->|Best of N| BoN["Best of N Sampling
        • Generate N Responses
        • Select Best"]

    SingleTech -->|Mixture of Agents| MoA["Mixture of Agents
        • Multiple Perspectives
        • Combine Insights"]

    SingleTech -->|Monte Carlo| MCTS["Monte Carlo Tree Search
        • Simulate Paths
        • Select Best Action"]

    SingleTech -->|Round Trip| RTO["Round Trip Optimisation
        • Generate
        • Verify
        • Refine"]

    SingleTech -->|Self Consistency| SC["Self Consistency
        • Multiple Attempts
        • Find Consensus"]

    SingleTech -->|Plan Search| PS["Plan Search
        • Generate Plans
        • Evaluate
        • Execute Best"]

    SingleTech -->|LEAP| LEAP["LEAP
        • Learn from Examples
        • Apply Principles"]

    SingleTech -->|ReRead| RE2["ReRead
        • Initial Read
        • Second Pass
        • Combine Insights"]

    SingleTech -->|R*| RStar["R* Algorithm
        • Depth Search
        • Multiple Rollouts"]

    SingleTech -->|Z3| Z3["Z3 Solver
        • Logical Analysis
        • Theorem Proving"]

    SingleTech -->|PV Game| PVG["Prover-Verifier Game
        • Generate Proof
        • Verify
        • Iterate"]

    %% Plugins
    SingleTech -->|Plugins| Plugins["Optional Plugins
        • Memory
        • Privacy
        • URL Reader
        • Code Executor"]

    %% Merge optimisation paths
    CoT & BoN & MoA & MCTS & RTO & SC & PS & LEAP & RE2 & RStar & Z3 & PVG & Plugins --> ProcessResult
    SeqTechs & ParTechs --> ProcessResult

    ProcessResult[Process Result] --> ResponseType{Response<br/>Type}

    %% Response handling
    ResponseType -->|Stream| StreamResp["Stream Processing
        • Setup Stream
        • Process Chunks
        • Send Events"]

    ResponseType -->|Regular| RegularResp["Regular Response
        • Format Result
        • Add Metadata
        • Send JSON"]

    StreamResp & RegularResp --> ReturnResp([Return Response])

    %% Styling
    classDef process fill:#90EE90,stroke:#333,stroke-width:2px
    classDef decision fill:#FFB6C1,stroke:#333,stroke-width:2px
    classDef endpoint fill:#87CEEB,stroke:#333,stroke-width:2px
    classDef error fill:#FF6B6B,stroke:#333,stroke-width:2px
    classDef technique fill:#DDA0DD,stroke:#333,stroke-width:2px

    class Start,ReturnResp endpoint
    class Auth,CheckOpt,CheckApp,CombinedOps,SingleTech,ResponseType decision
    class ParseReq,ProcessResult,StreamResp,RegularResp process
    class Return401 error
    class CoT,BoN,MoA,MCTS,RTO,SC,PS,LEAP,RE2,RStar,Z3,PVG,Plugins technique
    class SeqProcess,ParProcess,SeqTechs,ParTechs process
```
