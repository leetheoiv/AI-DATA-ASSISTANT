
#-----------------------------------------------------------------------------------------------------------------#
#   Create a Tool function                                                                                              #
#-----------------------------------------------------------------------------------------------------------------#
# Required Parameters:
        # "parameters": {
        #     "type": "object",
        #     "properties": {
        #         "lat": {
        #             "type": "number", 
        #             "description": "Latitude of the location"
        #         },
        #         "long": {
        #             "type": "number", 
        #             "description": "Longitude of the location"
        #         }
        #     },
        #     "required": ["lat", "long"],
        #     "additionalProperties": False
        # },

def create_tool(name: str, description: str, parameters: dict = None, tool_type: str = "function", tools: list = None, strict: bool = True) -> dict:
    if tool_type == "group":
        # Namespace structure: Contains a list of other tools
        return {
            "type": "namespace",
            "name": name,
            "description": description,
            "tools": tools or []
        }
    else:
        # Standard Function structure: Requires the nested 'function' key
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
                "strict": strict
            }
        }