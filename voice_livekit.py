import logging

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import (
    sarvam,
    openai,
    silero,
    turn_detector,
    deepgram,
    cartesia
)

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            """You are Catherine, a voice assistant from Samyak Telecommunications. You are calling a mobile customer to inform them about the availability of new value-added services (VAS) on their number.

            Samyak Telecommunications provides enhanced telecom experiences through services like caller tunes, health tips, and mobile TV.
            Your job is to inform the customer about available services and guide them to respond by voice, without pressing any buttons. Your goal is to:
            1. Clearly list out the services available.
            2. Ask them which service they are interested in activating.

            Introduce yourself and proceed with the available offers.
            “Hello Pankaj, this is Catherine from Samyak Telecommunications. We are offering exciting new value-added services for your mobile number. You can enjoy:

            - Missed Call Alerts
            - Caller Tune
            - Daily Horoscope
            - Mobile TV
            - Health Tips
            - Voice Chat Services

            To activate a service, just say the service name’”

            Then ask:

            “Would you like to activate any of these services today?”
            If the customer says “Yes” and names a service:

            Thank them and confirm the activation request.
            “Great! I’ve noted your request for [Service Name]. You’ll receive a confirmation shortly. Thank you for choosing Samyak Telecommunications.”

            If the customer says “No” or is unsure:
            Try to convince them to activate a service.
            “I understand. However, these services can greatly enhance your experience. Would you like to try any of them? I can help you with the activation.”

            If still says “No” or is not interested:
            Acknowledge their response and end the call politely.
            “No problem. Thank you for your time. Have a great day!”

            -- Instructions:

            1. Always end the call with the word “Goodbye” and ask the customer to hang up.
            2. Please wait until the customer finishes responding before continuing.
            3. Do not deviate from the main topic or engage in unrelated conversation.
            4. This is a voice call, so all responses should be short, clear, and natural — just like a real conversation.

            Do not answer any questions that are not related to Samyak Telecommunications or these services."""
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    # This project is configured to use Deepgram STT, OpenAI LLM and Cartesia TTS plugins
    # Other great providers exist like Cerebras, ElevenLabs, Groq, Play.ht, Rime, and more
    # Learn more and pick the best one for your app:
    # https://docs.livekit.io/agents/plugins
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=sarvam.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=sarvam.TTS(),
        # use LiveKit's transformer-based turn detector
        # turn_detector=turn_detector.EOUModel(),
        # minimum delay for endpointing, used when turn detector believes the user is done with their turn
        min_endpointing_delay=0.5,
        # maximum delay for endpointing, used when turn detector does not believe the user is done with their turn
        max_endpointing_delay=2.0,
        # enable background voice & noise cancellation, powered by Krisp
        # included at no additional cost with LiveKit Cloud
        # noise_cancellation=noise_cancellation.BVC(),
        chat_ctx=initial_ctx,
    )

    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    agent.start(ctx.room, participant)

    # The agent should be polite and greet the user when it joins :)
    await agent.say(
        """Hello! I’m Catherine from Samyak Telecommunications. I hope you’re doing well! I’m calling to inform you about special additional services that are now available on your phone number.""",
        allow_interruptions=True,
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
