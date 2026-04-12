from fastapi import FastAPI

app = FastAPI()


# this is how we define a path in fastapi. the @app.get("/") means that this function will be called when we make a GET request to the root URL ("/"). the function read_root() will return a JSON response with the content {"Hello": "World"}.
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Routes handle different HTTP methods (GET, POST, etc.) and paths. For example, @app.get("/items/{item_id}") defines a route that accepts GET requests to /items/{item_id}, where {item_id} is a path parameter. The function read_item() will be called with the value of item_id when a request is made to that path.
@app.post("/items/{item_id}")
def create_item(item_id: int, item: dict):
    items = []
    items.append({"id": item_id, "data": item})
    return items

# FastAPI makes it easy to raise errors with custom status codes and messages. For example, if we want to raise a 404 error when an item is not found, we can use the HTTPException class from fastapi.exceptions.
from fastapi import HTTPException

# Request and Path Parameters: FastAPI allows you to define parameters in your path and query strings. For example, you can define a path parameter like {item_id} and a query parameter like ?q=search.

# Interactive Documentation: FastAPI automatically generates interactive API documentation using Swagger UI and ReDoc. You can access it at /docs or /redoc.