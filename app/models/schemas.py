# from pydantic import BaseModel, Field
# from typing import List, Optional

# class SearchRequest(BaseModel):
#     query: str = Field(..., min_length=2)
#     top_k: int = Field(default=5, ge=1, le=20)

# class SearchResult(BaseModel):
#     text: str
#     score: float
#     document_id: str
#     document_name: str
#     page_number: Optional[int] = None
#     chunk_id: str
#     source: str

# class SearchResponse(BaseModel):
#     query: str
#     results: List[SearchResult]

# class IngestResponse(BaseModel):
#     document_id: str
#     document_name: str
#     pages: int
#     chunks: int
#     message: str


from typing import Optional

from pydantic import BaseModel, Field


# =========================================================
# CHAT REQUEST
# =========================================================

class ChatRequest(BaseModel):
    conversation_id: Optional[int] = None

    query: str = Field(
        ...,
        min_length=1,
        description="User's question",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of documents to retrieve",
    )


# =========================================================
# CHAT RESPONSE
# =========================================================

class ChatResponse(BaseModel):
    success: bool
    conversation_id: int
    answer: str
    results: list = []


# =========================================================
# SIMULATOR SCHEMAS
# =========================================================

class SimulatorConfig(BaseModel):
    persona: str = Field(default="calm", description="Customer persona (calm, angry, etc.)")
    scenario: str = Field(default="general inquiry", description="The support scenario")
    initial_emotion: str = Field(default="neutral", description="Starting emotional state")
    current_emotion: str = Field(default="neutral", description="Current emotional state")
    issue_severity: str = Field(default="low", description="Severity of the issue")
    patience_level: str = Field(default="high", description="Customer's patience level")
    expected_resolution: str = Field(default="information", description="What the customer wants")


class SimulatorTurnRequest(BaseModel):
    conversation_id: Optional[int] = None
    agent_message: str = Field(..., description="The support agent's response")
    config: SimulatorConfig


class SimulatorTurnResponse(BaseModel):
    success: bool
    conversation_id: int
    customer_message: str = Field(..., description="The simulated customer's next message")
    current_emotion: str = Field(..., description="Updated emotional state")
    patience_level: str = Field(..., description="Updated patience level")