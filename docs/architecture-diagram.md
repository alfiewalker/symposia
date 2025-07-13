# 🏗️ Symposia Architecture Diagram

## System Overview

The Symposia framework implements a committee-based AI validation system that uses multiple LLM services to validate AI-generated content through structured deliberation and voting.

---

## High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Interface]
        API[Direct API]
        CONFIG[Configuration Files]
    end
    
    subgraph "Core Orchestration"
        FACTORY[Committee Factory]
        COMMITTEE[Committee]
        STRATEGY[Voting Strategy]
        REPUTATION[Reputation Manager]
    end
    
    subgraph "Committee Members"
        MEMBER1[Skeptical Scientist]
        MEMBER2[Optimistic Innovator]
        MEMBER3[Pragmatic Realist]
    end
    
    subgraph "LLM Services"
        OPENAI[OpenAI Service]
        CLAUDE[Claude Service]
        GEMINI[Gemini Service]
    end
    
    subgraph "External APIs"
        OPENAI_API[OpenAI API]
        ANTHROPIC_API[Anthropic API]
        GOOGLE_API[Google API]
    end
    
    subgraph "Data & Utilities"
        CACHE[Simple Cache]
        PARSER[JSON Parser]
        RESULT[Deliberation Result]
    end
    
    %% User Interface to Core
    CLI --> FACTORY
    API --> FACTORY
    CONFIG --> FACTORY
    
    %% Core Orchestration
    FACTORY --> COMMITTEE
    COMMITTEE --> STRATEGY
    COMMITTEE --> REPUTATION
    
    %% Committee to Members
    COMMITTEE --> MEMBER1
    COMMITTEE --> MEMBER2
    COMMITTEE --> MEMBER3
    
    %% Members to Services
    MEMBER1 --> OPENAI
    MEMBER2 --> CLAUDE
    MEMBER3 --> GEMINI
    
    %% Services to External APIs
    OPENAI --> OPENAI_API
    CLAUDE --> ANTHROPIC_API
    GEMINI --> GOOGLE_API
    
    %% Data Flow
    CACHE --> OPENAI
    CACHE --> CLAUDE
    CACHE --> GEMINI
    
    PARSER --> COMMITTEE
    RESULT --> CLI
    RESULT --> API
    
    classDef userInterface fill:#e1f5fe
    classDef core fill:#f3e5f5
    classDef members fill:#e8f5e8
    classDef services fill:#fff3e0
    classDef external fill:#ffebee
    classDef data fill:#f1f8e9
    
    class CLI,API,CONFIG userInterface
    class FACTORY,COMMITTEE,STRATEGY,REPUTATION core
    class MEMBER1,MEMBER2,MEMBER3 members
    class OPENAI,CLAUDE,GEMINI services
    class OPENAI_API,ANTHROPIC_API,GOOGLE_API external
    class CACHE,PARSER,RESULT data
```

---

## Detailed Component Architecture

```mermaid
graph LR
    subgraph "Configuration Layer"
        YAML[YAML Config]
        ENV[Environment Variables]
        MODELS[Pydantic Models]
    end
    
    subgraph "Factory Layer"
        FACTORY[Committee Factory]
        PROVIDER_MAP[Provider Mapping]
        STRATEGY_MAP[Strategy Mapping]
    end
    
    subgraph "Committee Layer"
        COMMITTEE[Committee]
        MEMBERS[Committee Members]
        VOTING[Voting Strategy]
        REPUTATION[Reputation Manager]
    end
    
    subgraph "Service Layer"
        BASE[LLM Service Base]
        OPENAI[OpenAI Service]
        CLAUDE[Claude Service]
        GEMINI[Gemini Service]
    end
    
    subgraph "Utility Layer"
        CACHE[Simple Cache]
        PARSER[JSON Parser]
        RESULT[Result Handler]
    end
    
    %% Configuration Flow
    YAML --> MODELS
    ENV --> MODELS
    MODELS --> FACTORY
    
    %% Factory Flow
    FACTORY --> PROVIDER_MAP
    FACTORY --> STRATEGY_MAP
    FACTORY --> COMMITTEE
    
    %% Committee Flow
    COMMITTEE --> MEMBERS
    COMMITTEE --> VOTING
    COMMITTEE --> REPUTATION
    
    %% Service Flow
    BASE --> OPENAI
    BASE --> CLAUDE
    BASE --> GEMINI
    
    %% Utility Flow
    CACHE --> BASE
    PARSER --> COMMITTEE
    RESULT --> COMMITTEE
    
    classDef config fill:#e3f2fd
    classDef factory fill:#f3e5f5
    classDef committee fill:#e8f5e8
    classDef service fill:#fff3e0
    classDef utility fill:#f1f8e9
    
    class YAML,ENV,MODELS config
    class FACTORY,PROVIDER_MAP,STRATEGY_MAP factory
    class COMMITTEE,MEMBERS,VOTING,REPUTATION committee
    class BASE,OPENAI,CLAUDE,GEMINI service
    class CACHE,PARSER,RESULT utility
```

---

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Factory
    participant Committee
    participant Member1
    participant Member2
    participant Member3
    participant LLMService
    participant ExternalAPI
    participant Parser
    participant Strategy
    participant Result
    
    User->>CLI: Submit validation request
    CLI->>Factory: Load configuration
    Factory->>Committee: Create committee with members
    
    par Parallel Member Voting
        Committee->>Member1: Cast vote
        Member1->>LLMService: Query LLM
        LLMService->>ExternalAPI: API call
        ExternalAPI-->>LLMService: Response
        LLMService-->>Member1: Structured response
        Member1-->>Committee: Vote + reasoning
        
        Committee->>Member2: Cast vote
        Member2->>LLMService: Query LLM
        LLMService->>ExternalAPI: API call
        ExternalAPI-->>LLMService: Response
        LLMService-->>Member2: Structured response
        Member2-->>Committee: Vote + reasoning
        
        Committee->>Member3: Cast vote
        Member3->>LLMService: Query LLM
        LLMService->>ExternalAPI: API call
        ExternalAPI-->>LLMService: Response
        LLMService-->>Member3: Structured response
        Member3-->>Committee: Vote + reasoning
    end
    
    Committee->>Parser: Parse JSON responses
    Parser-->>Committee: Structured votes
    
    Committee->>Strategy: Tally votes
    Strategy-->>Committee: Final decision
    
    Committee->>Result: Create deliberation result
    Result-->>Committee: Complete result
    
    Committee-->>CLI: Return result
    CLI-->>User: Display validation outcome
```

---

## Component Details

### 🔧 Core Components

| **Component** | **Purpose** | **Key Features** |
|---------------|-------------|------------------|
| **Committee Factory** | Creates committees from configuration | Provider mapping, strategy selection |
| **Committee** | Orchestrates deliberation process | Member management, voting coordination |
| **Committee Member** | Individual AI expert | Role-based reasoning, vote casting |
| **Voting Strategy** | Aggregates member votes | Weighted majority, mean, median |
| **Reputation Manager** | Tracks member reliability | Adaptive scoring, consistency bonus |

### 🌐 Service Layer

| **Service** | **Provider** | **Capabilities** |
|-------------|--------------|------------------|
| **OpenAI Service** | OpenAI GPT models | Chat completions, token tracking |
| **Claude Service** | Anthropic Claude | Message API, system prompts |
| **Gemini Service** | Google Gemini | Content generation, token counting |

### 📊 Data Flow

1. **Configuration Loading**: YAML config → Pydantic models → Factory
2. **Committee Creation**: Factory → Committee with members and strategies
3. **Parallel Voting**: All members query LLMs simultaneously
4. **Response Parsing**: JSON parsing → Structured vote data
5. **Vote Aggregation**: Strategy → Final decision
6. **Result Generation**: Complete trace with reasoning and costs

### 🛡️ Error Handling

- **Graceful Cost Calculation**: Fallback to 0.0 on calculation errors
- **Retry Logic**: Exponential backoff for API failures
- **Caching**: Reduces API calls and improves performance
- **Validation**: Pydantic models ensure configuration integrity

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV_CONFIG[Local Config]
        DEV_ENV[.env.local]
        DEV_EXAMPLE[Example Scripts]
    end
    
    subgraph "Production Environment"
        PROD_CONFIG[Production Config]
        PROD_ENV[Environment Variables]
        PROD_API[API Endpoints]
    end
    
    subgraph "Infrastructure"
        CACHE_SERVICE[Redis Cache]
        LOGGING[Logging Service]
        MONITORING[Monitoring]
    end
    
    DEV_CONFIG --> DEV_EXAMPLE
    DEV_ENV --> DEV_EXAMPLE
    
    PROD_CONFIG --> PROD_API
    PROD_ENV --> PROD_API
    
    PROD_API --> CACHE_SERVICE
    PROD_API --> LOGGING
    PROD_API --> MONITORING
    
    classDef dev fill:#e8f5e8
    classDef prod fill:#fff3e0
    classDef infra fill:#f3e5f5
    
    class DEV_CONFIG,DEV_ENV,DEV_EXAMPLE dev
    class PROD_CONFIG,PROD_ENV,PROD_API prod
    class CACHE_SERVICE,LOGGING,MONITORING infra
```

---

*Architecture diagram generated for Symposia Committee Validation System*  
*Version: 1.0* 