"""Hchat chat wrapper."""

from __future__ import annotations

import json
import logging
import os
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

import aiohttp
import requests

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.chat_models import (
    BaseChatModel,
    agenerate_from_stream,
    generate_from_stream,
)
from langchain_core.language_models.llms import create_base_retry_decorator
from langchain_core.messages import (
    AIMessageChunk,
    BaseMessage,
    BaseMessageChunk,
    ChatMessageChunk,
    FunctionMessageChunk,
    HumanMessageChunk,
    SystemMessageChunk,
    ToolMessageChunk,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.pydantic_v1 import BaseModel, Field, root_validator
from langchain_core.runnables import Runnable
from langchain_core.utils import (
    get_from_dict_or_env,
    get_pydantic_field_names,
    pre_init,
)

from langchain_community.adapters.openai import (
    convert_dict_to_message,
    convert_message_to_dict,
)

logger = logging.getLogger(__name__)


def _convert_delta_to_message_chunk(
    _dict: Mapping[str, Any], default_class: Type[BaseMessageChunk]
) -> BaseMessageChunk:
    role = _dict.get("role")
    content = _dict.get("content") or ""
    additional_kwargs: Dict = {}
    if _dict.get("function_call"):
        function_call = dict(_dict["function_call"])
        if "name" in function_call and function_call["name"] is None:
            function_call["name"] = ""
        additional_kwargs["function_call"] = function_call
    if _dict.get("tool_calls"):
        additional_kwargs["tool_calls"] = _dict["tool_calls"]

    if role == "user" or default_class == HumanMessageChunk:
        return HumanMessageChunk(content=content)
    elif role == "assistant" or default_class == AIMessageChunk:
        return AIMessageChunk(content=content, additional_kwargs=additional_kwargs)
    elif role == "system" or default_class == SystemMessageChunk:
        return SystemMessageChunk(content=content)
    elif role == "function" or default_class == FunctionMessageChunk:
        return FunctionMessageChunk(content=content, name=_dict["name"])
    elif role == "tool" or default_class == ToolMessageChunk:
        return ToolMessageChunk(content=content, tool_call_id=_dict["tool_call_id"])
    elif role or default_class == ChatMessageChunk:
        return ChatMessageChunk(content=content, role=role)  # type: ignore[arg-type]
    else:
        return default_class(content=content)  # type: ignore[call-arg]


def _create_retry_decorator(
    llm: ChatHchat,
    run_manager: Optional[
        Union[AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun]
    ] = None,
) -> Callable[[Any], Any]:
    """Create a retry decorator for HChat API calls."""
    
    errors = [
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException,
    ]
    return create_base_retry_decorator(
        error_types=errors, max_retries=llm.max_retries, run_manager=run_manager
    )


async def acompletion_with_retry(
    llm: ChatHchat,
    run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
    **kwargs: Any,
) -> Any:
    """Use tenacity to retry the async completion call."""
    retry_decorator = _create_retry_decorator(llm, run_manager=run_manager)

    @retry_decorator
    async def _completion_with_retry(**kwargs: Any) -> Any:
        # Prepare the request payload
        payload = {
            "model": llm.model_name,
            **kwargs,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm.hchat_api_key}",
        }
        
        # Handle streaming
        if kwargs.get("stream", False):
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{llm.hchat_api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=llm.request_timeout,
                ) as response:
                    response.raise_for_status()
                    async for line in response.content:
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith(b"data: "):
                            line = line[6:]  # Remove "data: " prefix
                            if line == b"[DONE]":
                                break
                            try:
                                chunk = json.loads(line)
                                yield chunk
                            except json.JSONDecodeError:
                                logger.error(f"Error parsing stream: {line}")
        else:
            # Non-streaming request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{llm.hchat_api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=llm.request_timeout,
                ) as response:
                    response.raise_for_status()
                    return await response.json()

    return await _completion_with_retry(**kwargs)


class ChatHchat(BaseChatModel):
    """HChat large language models API.

    To use, you should have the environment variable ``HCHAT_API_KEY`` set with your 
    API key, or pass it as a parameter.

    Example:
        .. code-block:: python

            from langchain_community.chat_models import ChatHchat
            hchat = ChatHchat(model="gpt-3.5-turbo")
    """

    @property
    def lc_secrets(self) -> Dict[str, str]:
        return {"hchat_api_key": "HCHAT_API_KEY"}

    @classmethod
    def get_lc_namespace(cls) -> List[str]:
        """Get the namespace of the langchain object."""
        return ["langchain", "chat_models", "hchat"]

    @property
    def lc_attributes(self) -> Dict[str, Any]:
        attributes: Dict[str, Any] = {}

        if self.hchat_api_base:
            attributes["hchat_api_base"] = self.hchat_api_base

        return attributes

    @classmethod
    def is_lc_serializable(cls) -> bool:
        """Return whether this model can be serialized by Langchain."""
        return True

    model_name: str = Field(default="gpt-3.5-turbo", alias="model")
    """Model name to use."""
    temperature: float = 0.7
    """What sampling temperature to use."""
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    """Holds any model parameters valid for API call not explicitly specified."""
    hchat_api_key: Optional[str] = Field(default=None, alias="api_key")
    """Automatically inferred from env var `HCHAT_API_KEY` if not provided."""
    hchat_api_base: str = Field(default="https://api.hchat.com", alias="base_url")
    """Base URL path for API requests."""
    request_timeout: Union[float, Tuple[float, float], Any, None] = Field(
        default=None, alias="timeout"
    )
    """Timeout for requests to HChat API. Default is 60 seconds."""
    max_retries: int = Field(default=2)
    """Maximum number of retries to make when generating."""
    streaming: bool = False
    """Whether to stream the results or not."""
    n: int = 1
    """Number of chat completions to generate for each prompt."""
    max_tokens: Optional[int] = None
    """Maximum number of tokens to generate."""

    class Config:
        allow_population_by_field_name = True

    @root_validator(pre=True)
    def build_extra(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Build extra kwargs from additional params that were passed in."""
        all_required_field_names = get_pydantic_field_names(cls)
        extra = values.get("model_kwargs", {})
        for field_name in list(values):
            if field_name in extra:
                raise ValueError(f"Found {field_name} supplied twice.")
            if field_name not in all_required_field_names:
                logger.warning(
                    f"""WARNING! {field_name} is not default parameter.
                    {field_name} was transferred to model_kwargs.
                    Please confirm that {field_name} is what you intended."""
                )
                extra[field_name] = values.pop(field_name)

        invalid_model_kwargs = all_required_field_names.intersection(extra.keys())
        if invalid_model_kwargs:
            raise ValueError(
                f"Parameters {invalid_model_kwargs} should be specified explicitly. "
                f"Instead they were passed in as part of `model_kwargs` parameter."
            )

        values["model_kwargs"] = extra
        return values

    @pre_init
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key exists in environment."""
        if values["n"] < 1:
            raise ValueError("n must be at least 1.")
        if values["n"] > 1 and values["streaming"]:
            raise ValueError("n must be 1 when streaming.")

        values["hchat_api_key"] = get_from_dict_or_env(
            values, "hchat_api_key", "HCHAT_API_KEY"
        )
        
        # Set default timeout if not provided
        if values.get("request_timeout") is None:
            values["request_timeout"] = 60.0
            
        return values

    @property
    def _default_params(self) -> Dict[str, Any]:
        """Get the default parameters for calling HChat API."""
        params = {
            "model": self.model_name,
            "stream": self.streaming,
            "n": self.n,
            "temperature": self.temperature,
            **self.model_kwargs,
        }
        if self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens
        return params

    def completion_with_retry(
        self, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any
    ) -> Any:
        """Use tenacity to retry the completion call."""
        retry_decorator = _create_retry_decorator(self, run_manager=run_manager)

        @retry_decorator
        def _completion_with_retry(**kwargs: Any) -> Any:
            # Prepare the request payload
            payload = {
                "model": self.model_name,
                **kwargs,
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.hchat_api_key}",
            }
            
            # Handle streaming
            if kwargs.get("stream", False):
                response = requests.post(
                    f"{self.hchat_api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.request_timeout,
                    stream=True,
                )
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith(b"data: "):
                        line = line[6:]  # Remove "data: " prefix
                        if line == b"[DONE]":
                            break
                        try:
                            chunk = json.loads(line)
                            yield chunk
                        except json.JSONDecodeError:
                            logger.error(f"Error parsing stream: {line}")
            else:
                # Non-streaming request
                response = requests.post(
                    f"{self.hchat_api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.request_timeout,
                )
                response.raise_for_status()
                return response.json()

        return _completion_with_retry(**kwargs)

    def _combine_llm_outputs(self, llm_outputs: List[Optional[dict]]) -> dict:
        overall_token_usage = {}
        for output in llm_outputs:
            if output is None:
                # Happens in streaming
                continue
            token_usage = output.get("token_usage", {})
            if token_usage:
                for k, v in token_usage.items():
                    if k in overall_token_usage:
                        overall_token_usage[k] = overall_token_usage[k] + v
                    else:
                        overall_token_usage[k] = v
        return {"token_usage": overall_token_usage, "model_name": self.model_name}

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        message_dicts, params = self._create_message_dicts(messages, stop)
        params = {**params, **kwargs, "stream": True}

        default_chunk_class = AIMessageChunk
        for chunk in self.completion_with_retry(
            messages=message_dicts, run_manager=run_manager, **params
        ):
            if len(chunk["choices"]) == 0:
                continue
            choice = chunk["choices"][0]
            if choice.get("delta") is None:
                continue
            chunk = _convert_delta_to_message_chunk(
                choice["delta"], default_chunk_class
            )
            finish_reason = choice.get("finish_reason")
            generation_info = (
                dict(finish_reason=finish_reason) if finish_reason is not None else None
            )
            default_chunk_class = chunk.__class__
            cg_chunk = ChatGenerationChunk(
                message=chunk, generation_info=generation_info
            )
            if run_manager:
                run_manager.on_llm_new_token(cg_chunk.text, chunk=cg_chunk)
            yield cg_chunk

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        stream: Optional[bool] = None,
        **kwargs: Any,
    ) -> ChatResult:
        should_stream = stream if stream is not None else self.streaming
        if should_stream:
            stream_iter = self._stream(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )
            return generate_from_stream(stream_iter)
        message_dicts, params = self._create_message_dicts(messages, stop)
        params = {
            **params,
            **({"stream": stream} if stream is not None else {}),
            **kwargs,
        }
        response = self.completion_with_retry(
            messages=message_dicts, run_manager=run_manager, **params
        )
        return self._create_chat_result(response)

    def _create_message_dicts(
        self, messages: List[BaseMessage], stop: Optional[List[str]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        params = self._client_params
        if stop is not None:
            if "stop" in params:
                raise ValueError("`stop` found in both the input and default params.")
            params["stop"] = stop
        message_dicts = [convert_message_to_dict(m) for m in messages]
        return message_dicts, params

    def _create_chat_result(self, response: dict) -> ChatResult:
        generations = []
        for res in response["choices"]:
            message = convert_dict_to_message(res["message"])
            generation_info = dict(finish_reason=res.get("finish_reason"))
            gen = ChatGeneration(
                message=message,
                generation_info=generation_info,
            )
            generations.append(gen)
        token_usage = response.get("usage", {})
        llm_output = {
            "token_usage": token_usage,
            "model_name": self.model_name,
        }
        return ChatResult(generations=generations, llm_output=llm_output)

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        message_dicts, params = self._create_message_dicts(messages, stop)
        params = {**params, **kwargs, "stream": True}

        default_chunk_class = AIMessageChunk
        async for chunk in await acompletion_with_retry(
            self, messages=message_dicts, run_manager=run_manager, **params
        ):
            if len(chunk["choices"]) == 0:
                continue
            choice = chunk["choices"][0]
            if choice.get("delta") is None:
                continue
            chunk = _convert_delta_to_message_chunk(
                choice["delta"], default_chunk_class
            )
            finish_reason = choice.get("finish_reason")
            generation_info = (
                dict(finish_reason=finish_reason) if finish_reason is not None else None
            )
            default_chunk_class = chunk.__class__
            cg_chunk = ChatGenerationChunk(
                message=chunk, generation_info=generation_info
            )
            if run_manager:
                await run_manager.on_llm_new_token(token=cg_chunk.text, chunk=cg_chunk)
            yield cg_chunk

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        stream: Optional[bool] = None,
        **kwargs: Any,
    ) -> ChatResult:
        should_stream = stream if stream is not None else self.streaming
        if should_stream:
            stream_iter = self._astream(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )
            return await agenerate_from_stream(stream_iter)

        message_dicts, params = self._create_message_dicts(messages, stop)
        params = {
            **params,
            **({"stream": stream} if stream is not None else {}),
            **kwargs,
        }
        response = await acompletion_with_retry(
            self, messages=message_dicts, run_manager=run_manager, **params
        )
        return self._create_chat_result(response)

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {**{"model_name": self.model_name}, **self._default_params}

    @property
    def _client_params(self) -> Dict[str, Any]:
        """Get the parameters used for the Hchat client."""
        return {**self._default_params}

    def _get_invocation_params(
        self, stop: Optional[List[str]] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """Get the parameters used to invoke the model."""
        return {
            "model": self.model_name,
            **super()._get_invocation_params(stop=stop),
            **self._default_params,
            **kwargs,
        }

    @property
    def _llm_type(self) -> str:
        """Return type of chat model."""
        return "hchat"

    def bind_functions(
        self,
        functions: Sequence[Union[Dict[str, Any], Type[BaseModel], Callable]],
        function_call: Optional[str] = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind functions (and other objects) to this chat model.

        Args:
            functions: A list of function definitions to bind to this chat model.
                Can be a dictionary, pydantic model, or callable. Pydantic
                models and callables will be automatically converted to
                their schema dictionary representation.
            function_call: Which function to require the model to call.
                Must be the name of the single provided function or
                "auto" to automatically determine which function to call
                (if any).
            kwargs: Any additional parameters to pass to the
                :class:`~langchain.runnable.Runnable` constructor.
        """
        from langchain.chains.openai_functions.base import convert_to_openai_function

        formatted_functions = [convert_to_openai_function(fn) for fn in functions]
        if function_call is not None:
            if len(formatted_functions) != 1:
                raise ValueError(
                    "When specifying `function_call`, you must provide exactly one "
                    "function."
                )
            if formatted_functions[0]["name"] != function_call:
                raise ValueError(
                    f"Function call {function_call} was specified, but the only "
                    f"provided function was {formatted_functions[0]['name']}."
                )
            function_call_ = {"name": function_call}
            kwargs = {**kwargs, "function_call": function_call_}
        return super().bind(
            functions=formatted_functions,
            **kwargs,
        )
