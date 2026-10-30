# -*- coding: utf-8 -*-
"""从项目根目录的 .env 文件加载环境变量（本地开发凭证，已被 .gitignore 忽略，勿提交）。

真实环境变量优先：已存在的环境变量不会被 .env 覆盖（setdefault），
因此生产环境仍可直接通过 export 注入凭证，.env 仅作本地默认值兜底。
"""
import os

_ENV_LOADED = False


def load_env(env_path=None):
    """加载 .env 到 os.environ（幂等，多次调用只读取一次）。"""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True

    path = env_path or _default_env_path()
    if not path or not os.path.isfile(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                # 去掉首尾成对的引号
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key:
                    os.environ.setdefault(key, value)
    except Exception:
        # .env 读取失败不应阻塞服务启动
        pass


def _default_env_path():
    # 本文件位于 app/config/ 下，向上两级即为项目根目录
    here = os.path.dirname(os.path.abspath(__file__))      # .../app/config
    root = os.path.dirname(os.path.dirname(here))           # 项目根
    return os.path.join(root, '.env')
