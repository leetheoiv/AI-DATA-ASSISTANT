
#-----------------------------------------------------------------------------------------------------------------#
#   Create a Tool function                                                                                              #
#-----------------------------------------------------------------------------------------------------------------#
# tools = [
#     {
#         "type:": "function",
#         "name": "get_csv_data",
#         "description": "Extracts data from a CSV file and returns it in a structured format.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "file_path": {
#                     "type": "string",
#                     "description": "The path to the CSV file to be processed."
#                 }
#             },
#             "required": ["file_path"]
#         }
#     }
# ]

def create_tool(type: str, name: str, description: str, parameters: dict, strict: str) -> dict:
    return {
        "type": type,
        "name": name,
        "description": description,
        "parameters": parameters,
        "strict":strict
    }