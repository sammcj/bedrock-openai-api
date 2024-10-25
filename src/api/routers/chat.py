from typing import Annotated
from fastapi import APIRouter, Depends, Body, HTTPException
from fastapi.responses import StreamingResponse

from api.auth import api_key_auth
from api.models.bedrock import BedrockModel
from api.schema import ChatRequest, ChatResponse, ChatStreamResponse
from api.setting import DEFAULT_MODEL, FALLBACK_MODEL, OPTILLM_ENABLED, OPTILLM_APPROACH

from ..optillm_adapter import OptillmAdapter

# Initialise the adapter
optillm = OptillmAdapter(enabled=OPTILLM_ENABLED, approach=OPTILLM_APPROACH)


def extract_optillm_approach(model: str, adapter: OptillmAdapter) -> tuple[str, str]:
    """Extract optillm approach from model name if present"""
    parts = model.split("-")
    if len(parts) > 1 and parts[0] in adapter._optimisers:
        return parts[0], "-".join(parts[1:])
    return None, model

router = APIRouter(
    prefix="/chat",
    dependencies=[Depends(api_key_auth)],
)

@router.post(
    "/completions",
    response_model=ChatResponse | ChatStreamResponse,
    response_model_exclude_unset=True,
)
async def chat_completions(
    chat_request: Annotated[
        ChatRequest,
        Body(
            examples=[
                {
                    "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello!"},
                    ],
                }
            ],
        ),
    ]
):

    # Optimise the request if optillm is enabled
    if OPTILLM_ENABLED:
        approach, base_model = extract_optillm_approach(chat_request.model, optillm)
        if approach:
            optillm.approach = approach
            chat_request.model = base_model

        optimised_request = await optillm.optimise_request(
            messages=chat_request.messages,
            model=chat_request.model,
            temperature=chat_request.temperature,
        )

        # Use the optimized request with your existing Bedrock client
        model = BedrockModel()
        if chat_request.stream:
            return StreamingResponse(
                content=model.chat_stream(optimised_request),
                media_type="text/event-stream",
            )
        return await model.chat(optimised_request)

    # Otherwise, use the original request
    else:
        model = BedrockModel()

        if (
            not chat_request.model
            or chat_request.model.strip() == ""
            or chat_request.model.lower().startswith("gpt-")
        ):
            chat_request.model = DEFAULT_MODEL

        try:
            model.validate(chat_request)
        except HTTPException:
            # If the requested model is not supported, fall back to the default model
            chat_request.model = FALLBACK_MODEL
            try:
                model.validate(chat_request)
            except HTTPException:
                # If even the fallback model is not supported, raise an error
                raise HTTPException(
                    status_code=500,
                    detail=f"Both requested model and fallback model are not supported. Please check your configuration.",
                )

        if chat_request.stream:
            return StreamingResponse(
                content=model.chat_stream(chat_request), media_type="text/event-stream"
            )
        return await model.chat(chat_request)
