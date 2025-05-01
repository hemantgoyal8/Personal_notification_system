import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter

from graphql_gateway.app.schemas_gql.schema import schema # Import the combined schema
from graphql_gateway.app.auth.context import get_context # Import the context dependency
from graphql_gateway.app.core.config import settings, logger # Import config and logger

app = FastAPI(
    title="GraphQL Gateway",
    description="Unified GraphQL API for the Personalized Notification System.",
    version="1.0.0"
)

# Setup GraphQL endpoint
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context, # Use our custom context getter
    graphiql=True # Enable GraphiQL interface at /graphql
)

app.include_router(graphql_app, prefix="/graphql")

# Optional: Generic Error Handling for non-GraphQL routes or context errors
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Handle exceptions that might occur *before* or *during* context creation,
    # or for non-GraphQL routes. Resolver errors are typically handled by Strawberry.
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred in the gateway."},
    )


# Startup / Shutdown events (optional, httpx client lifecycle handled in context getter)
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up GraphQL Gateway...")
    # Perform any other startup tasks if needed

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down GraphQL Gateway...")
    # Perform cleanup if needed

# Health check and root endpoints
@app.get("/health", tags=["Health Check"])
async def health_check():
    # Could add checks to ping downstream services if desired
    return {"status": "ok", "service": "GraphQL Gateway"}

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the GraphQL Gateway. Access the API at /graphql"}

# To run the service (from the 'personalized-notification-system' directory):
# uvicorn graphql_gateway.app.main:app --reload --port 8080