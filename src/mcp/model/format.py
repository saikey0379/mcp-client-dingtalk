def FormatMappingToolName(server_name: str, tool_name: str):
    return f"{server_name}__{tool_name}"


def GetServerAndToolName(mapping_tool_name: str):
    return mapping_tool_name.split("__")
