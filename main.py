# Util
import os
import asyncio
from fastapi import param_functions
from loguru import logger

# Pipecat
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import parse_telephony_websocket
from pipecat.serializers.exotel import ExotelFrameSerializer
from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService, InputParams
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
# Config
import config as cfg

DEFAULT_INSTRUCTIONS = cfg.DEFAULT_INSTRUCTIONS
GEMINI_VOICE = cfg.GEMINI_VOICE
GEMINI_MODEL = cfg.GEMINI_MODEL
VAD_CONFIDENCE = cfg.VAD_CONFIDENCE
VAD_START_SECS = cfg.VAD_START_SECS
VAD_STOP_SECS = cfg.VAD_STOP_SECS
VAD_MIN_VOLUME = cfg.VAD_MIN_VOLUME

if os.getenv("RAILWAY_SERVICE_NAME") is None:
    from dotenv import load_dotenv
    load_dotenv(override=True)


async def run_bot(transport: BaseTransport, handle_sigint: bool):
    logger.info(f"Starting bot")

    # System prompt from config
    instructions = DEFAULT_INSTRUCTIONS

    llm = GeminiLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model=GEMINI_MODEL,
        voice_id=GEMINI_VOICE,  # Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, and Zephyr
        system_instruction=instructions,
        
    )

    messages = []

    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),  # Websocket input from client
            context_aggregator.user(),  # User responses
            llm,  # LLM
            transport.output(),  # Websocket output to client
            context_aggregator.assistant(),  # Assistant spoken responses
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=8000,
            audio_out_sample_rate=8000,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected")
        # Kick off the conversation.
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=handle_sigint)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""

    transport_type, call_data = await parse_telephony_websocket(runner_args.websocket)
    logger.info(f"Auto-detected transport: {transport_type}")

    serializer = ExotelFrameSerializer(
        stream_sid=call_data["stream_id"],
        call_sid=call_data["call_id"],
    )

    transport = FastAPIWebsocketTransport(
        websocket=runner_args.websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(
                    confidence=VAD_CONFIDENCE,
                    start_secs=VAD_START_SECS,
                    stop_secs=VAD_STOP_SECS,
                    min_volume=VAD_MIN_VOLUME,
                )
            ),
            serializer=serializer,
        ),
    )

    handle_sigint = runner_args.handle_sigint

    await run_bot(transport, handle_sigint)


if __name__ == "__main__":
    from pipecat.runner.run import main
    # start a task to periodically update the context
  
    main()