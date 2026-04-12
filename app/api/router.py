"""
**Routes incoming requests to the appropriate endpoint handlers**

Creates a main router
Imports our endpoint module with its router
Adds the endpoint router with the prefix /events
Uses tags for documentation organization
Routes all requests that start with /events to our endpoint
"""


from fastapi import APIRouter
from app.api import endpoint


# Creates a main router
router = APIRouter()

# Adds the endpoint router with the prefix /events
router.include_router(endpoint.router, prefix="/analysis", tags=["analysis"])

