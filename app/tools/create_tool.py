#https://developers.openai.com/api/docs/guides/function-calling?strict-mode=enabled
#-----------------------------------------------------------------------------------------------------------------#
#   Create a Tool function                                                                                        #
#-----------------------------------------------------------------------------------------------------------------#
# Required Parameters:
    ## 1. Define a list of callable tools for the model
    # tools = [
    #     {
    #         "type": "function",
    #         "name": "get_horoscope",
    #         "description": "Get today's horoscope for an astrological sign.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "sign": {
    #                     "type": "string",
    #                     "description": "An astrological sign like Taurus or Aquarius",
    #                 },
    #             },
    #             "required": ["sign"],
    #         },
    #     },
    # ]

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
            "name": name,
            "description": description,
            "function": {
                "parameters": parameters,
                "strict": strict
            }
        }