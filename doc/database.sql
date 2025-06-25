CREATE TABLE mcp_users (
    id INTEGER PRIMARY KEY, -- 用户id
    user_id VARCHAR, -- 钉钉用户id
    user_name VARCHAR, -- 用户名
    mobile VARCHAR, -- 手机号
    provider_name VARCHAR, -- 提供商名称，如openai
    model VARCHAR, -- 模型名称，如gpt-4o
    api_key VARCHAR, -- 提供商的api key
    base_url VARCHAR, -- 提供商的base url
    language VARCHAR, -- 语言，如zh-cn
    role VARCHAR -- 角色，如devops
);


INSERT INTO mcp_users 
    (id, user_id, user_name, mobile, provider_name, model, api_key, base_url, language, role) 
VALUES 
    ('1',
     '1234567890',
     'username', # 用户名
     '18888888888', # 手机号
     'openai',
     'gpt-4o',
     'xxxxxxxx',
     'http://www.openai.com/vx',
     'zh-cn',
     'devops');