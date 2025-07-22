import json


def FormatJsonString(json_str):
    # 将 JSON 字符串解析为 Python 对象
    try:
        parsed_json = json.loads(json_str)
    except json.JSONDecodeError:
        return "Invalid JSON"

    # 将 Python 对象格式化为漂亮的多行 JSON 字符串
    formatted_json_str = json.dumps(parsed_json, indent=4, ensure_ascii=False)

    # 去掉最后一行换行符
    return formatted_json_str.rstrip('\n')


def CompactJsonString(formatted_json_str):
    # 将格式化的 JSON 字符串解析为 Python 对象
    try:
        parsed_json = json.loads(formatted_json_str)
    except json.JSONDecodeError:
        return "Invalid JSON"

    # 将 Python 对象转换为紧凑的单行 JSON 字符串
    compact_json_str = json.dumps(
        parsed_json, separators=(',', ':'), ensure_ascii=False)

    return compact_json_str
