from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import numpy as np
from app.api.router import router as process_router



# Create the fastapi app
app = FastAPI()

# Moves the data to the right aspi endpints
app.include_router(process_router)