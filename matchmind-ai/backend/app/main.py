"""FastAPI app that serves predictions, the agent endpoint, and the frontend."""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.agent import PROMPT_VERSION
from app.agent_runtime import AgentUnavailable, analyse
from app.config import Settings
from app.prediction import PredictionService, UnsupportedFixture
from app.schemas import AnalyseRequest, Analysis, Prediction, PredictionRequest
from app.telemetry import emit
from app.vertex_schema import VertexRequest

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logging.getLogger("matchmind").setLevel(logging.INFO)


def create_app(settings=None, predictor=None, analyser=analyse):
    """Create the application with its configured predictor and agent hooks."""
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        # Load the model once at startup and keep a small agent concurrency gate.
        app.state.predictor = predictor or PredictionService(config.artifact_dir)
        app.state.agent_slots = asyncio.Semaphore(4)
        yield

    app = FastAPI(title="MatchMind ADK", version="2.0.0", lifespan=lifespan, docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def headers(request: Request, call_next):
        # Bounds include chunked bodies; Pydantic separately limits the parsed message.
        # Reject oversized POST bodies before the app spends time parsing them.
        if request.method == "POST":
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 8192:
                    from starlette.responses import JSONResponse
                    return JSONResponse({"detail": "Request too large"}, status_code=413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'"
        return response

    @app.get("/health")
    def health():
        """Return a quick status check for the UI and deployment scripts."""
        return {"status": "healthy", "model_version": app.state.predictor.metadata["model_version"],
                "agent_enabled": config.agent_enabled, "gemini_model": config.gemini_model,
                "data_origin": app.state.predictor.metadata["data_origin"]}

    @app.get("/api/teams")
    def teams():
        """Expose the supported team names for the direct prediction form."""
        return {"teams": app.state.predictor.teams}

    @app.get("/api/model")
    def metadata():
        """Expose the saved model metadata for debugging and release checks."""
        return app.state.predictor.metadata

    @app.post("/api/predict", response_model=Prediction)
    async def direct(request: PredictionRequest):
        """Run the classifier directly without the agent layer."""
        start = time.perf_counter()
        try:
            result = await run_in_threadpool(app.state.predictor.predict, request.home_team, request.away_team)
        except UnsupportedFixture as error:
            raise HTTPException(422, "Use two different supported team names") from error
        emit("prediction_completed", request_id=str(uuid4()), status="complete",
             latency_ms=round((time.perf_counter()-start)*1000), model_version=result["model_version"])
        return result

    @app.post("/api/analyse", response_model=Analysis)
    async def agent_analysis(request: AnalyseRequest):
        """Let the ADK agent interpret the message and call prediction tools."""
        start = time.perf_counter()
        try:
            await asyncio.wait_for(app.state.agent_slots.acquire(), timeout=.1)
        except TimeoutError:
            raise HTTPException(429, "Agent busy. Retry shortly.")
        try:
            result = await analyser(app.state.predictor, config, request.message)
        except AgentUnavailable as error:
            emit("agent_request", status="unavailable", latency_ms=round((time.perf_counter()-start)*1000))
            raise HTTPException(503, str(error)) from error
        finally:
            app.state.agent_slots.release()
        emit("agent_request", request_id=result.request_id, status=result.status,
             latency_ms=round((time.perf_counter()-start)*1000),
             model_version=app.state.predictor.metadata["model_version"], prompt_version=PROMPT_VERSION,
             input_tokens=result.input_tokens, output_tokens=result.output_tokens,
             prediction_count=len(result.predictions), tool_count=len(result.tool_calls))
        return result

    @app.post("/api/vertex/predict")
    async def vertex_predict(request: VertexRequest):
        """Serve the classifier in the Vertex AI request format."""
        try:
            results = [await run_in_threadpool(app.state.predictor.predict, r.home_team, r.away_team)
                       for r in request.instances]
        except UnsupportedFixture as error:
            raise HTTPException(422, "Use supported team names") from error
        return {"predictions": results}

    # Production serves React and API on one origin; Vite proxies these routes in development.
    if config.static_dir.is_dir():
        app.mount("/", StaticFiles(directory=config.static_dir, html=True), name="frontend")
    return app


# Build the default app instance used by Uvicorn and tests.
app = create_app()
