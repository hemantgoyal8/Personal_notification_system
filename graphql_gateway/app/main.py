# graphql_gateway/app/main.py
import sys
import logging # For the logger used in the original code
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter # Strawberry's GraphQLRouter

# Corrected import for the schema
from .schemas_gql.schema import schema

# Corrected import for the context getter
# Assuming auth/context.py exists in graphql_gateway/app/auth/context.py
# If context.py is directly under graphql_gateway/app/, it would be from .context import get_context
# Looking at the repo, it seems context.py is in graphql_gateway/app/auth/context.py
from .auth.context import get_context

# Corrected import for config and logger
from .core.config import settings, logger # logger here is the one configured in core.config

# --- DEBUG PRINTS (can be removed once stable) ---
print(f"--- DEBUG INFO from /app/app/main.py (FULL VERSION) ---")
print(f"Current sys.path: {sys.path}")
print(f"__name__: {__name__}")
print(f"__package__: {__package__}")
print(f"--- END DEBUG INFO ---")
# --- END DEBUG PRINTS ---

app = FastAPI(
    title="GraphQL Gateway",
    description="Unified GraphQL API for the Personalized Notification System.",
    version="1.0.0"
)

# Setup GraphQL endpoint using GraphQLRouter
graphql_app_router = GraphQLRouter( # Renamed variable to avoid confusion with 'app'
    schema,
    context_getter=get_context, # Use our custom context getter
    graphiql=True # Enable GraphiQL interface at /graphql
)

app.include_router(graphql_app_router, prefix="/graphql")

# Optional: Generic Error Handling
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred in the gateway."},
    )

# Startup / Shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up GraphQL Gateway...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down GraphQL Gateway...")

# Health check and root endpoints
@app.get("/health", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "service": "GraphQL Gateway"}

@app.get("/", tags=["Root"])
async def read_root(): # This will override the simplified one if both exist
    return {"message": "Welcome to the GraphQL Gateway. Access the API at /graphql"}