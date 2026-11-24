#!/usr/bin/env python3
"""MCP-сервер каталога buddyooo.ru — поиск и карточки товаров для ИИ-ассистентов.

Два режима:
- по умолчанию: stdio — локальное подключение из Claude Desktop / Claude Code;
- --http: streamable-http на 127.0.0.1:8780 (путь /mcp) — публичный режим,
  ставится как сервис buddy-mcp.service и публикуется nginx'ом на
  https://mcp.buddyooo.ru/mcp — ОТКРЫТЫЙ эндпоинт без авторизации
  (любой ИИ-агент подключается сам), от флуда защищает rate-limit nginx
  (~10 r/s на IP).

Инструменты используют публичный API сайта; кэш 5 минут бережёт сайт
от частых одинаковых запросов.

Подключение (claude_desktop_config.json или .mcp.json проекта):

{
  "mcpServers": {
    "buddyooo": {
      "command": "/home/sn/apps/buddyooo.ru/venv/bin/python",
      "args": ["/home/sn/apps/buddyooo.ru/mcp_server.py"]
    }
  }
}

Удалённое подключение (любой MCP-клиент, без авторизации):

{
  "mcpServers": {
    "buddyooo": {
      "url": "https://mcp.buddyooo.ru/mcp"
    }
  }
}
"""
import argparse
import json
import os
import time

import httpx
from mcp.server.fastmcp import FastMCP

HOST = os.getenv('MCP_HOST', '127.0.0.1')
PORT = int(os.getenv('MCP_PORT', 8780))

BASE_URL = os.getenv('BUDDY_BASE_URL', 'https://buddyooo.ru')
TIMEOUT = 30
CACHE_TTL = 300  # секунд

mcp = FastMCP('buddyooo', host=HOST, port=PORT)

_cache = {}  # ключ -> (timestamp, данные)


def _cached(key, fetch):
    """Простой TTL-кэш для GET-запросов к сайту."""
    hit = _cache.get(key)
    now = time.time()
    if hit and now - hit[0] < CACHE_TTL:
        return hit[1]
    data = fetch()
    _cache[key] = (now, data)
    return data


def _get_json(path, params=None):
    resp = httpx.get(
        f'{BASE_URL}{path}',
        params=params,
        timeout=TIMEOUT,
        headers={'User-Agent': 'buddyooo-mcp/1.0', 'Accept': 'application/json'},
    )
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def search_products(query: str, limit: int = 10) -> str:
    """Нейросетевой поиск по каталогу buddyooo.ru (82 000+ товаров электротехники
    и стройматериалов). Понимает запросы обычным языком: «автомат на 16 ампер»,
    «кабель для прокладки в земле». Возвращает JSON-список: name, price (руб),
    stock (шт), alias (передайте в get_product для деталей), article, brand_name."""
    limit = max(1, min(int(limit), 100))
    data = _cached(('search', query, limit),
                   lambda: _get_json('/api/search', {'q': query, 'limit': limit}))
    results = [
        {
            'name': r.get('name', ''),
            'price': r.get('price'),
            'stock': r.get('stock', 0),
            'alias': r.get('alias', ''),
            'article': r.get('article', ''),
            'brand_name': r.get('brand_name', ''),
        }
        for r in data.get('results', [])
    ]
    return json.dumps(
        {'query': data.get('query', query), 'count': len(results), 'results': results},
        ensure_ascii=False, indent=1)


@mcp.tool()
def get_product(alias: str) -> str:
    """Карточка товара buddyooo.ru по alias (берётся из результатов search_products).
    Возвращает цену, наличие, характеристики, описание и URL страницы товара."""
    data = _cached(('product', alias),
                   lambda: _get_json(f'/api/product-info/{alias}'))
    return json.dumps(data, ensure_ascii=False, indent=1)


@mcp.tool()
def list_categories(limit: int = 50) -> str:
    """Топ категории каталога buddyooo.ru по количеству товаров.
    Возвращает JSON: name, alias (для ссылки /category/<alias>), product_count."""
    limit = max(1, min(int(limit), 200))
    data = _cached(('categories', limit),
                   lambda: _get_json('/api/categories', {'limit': limit}))
    return json.dumps(data, ensure_ascii=False, indent=1)


@mcp.resource('llms://full')
def llms_full() -> str:
    """Полная справка о магазине: условия заказа/оплаты/доставки, топ категории,
    примеры товаров с ценами, контакты."""
    resp = httpx.get(f'{BASE_URL}/llms-full.txt', timeout=TIMEOUT,
                     headers={'User-Agent': 'buddyooo-mcp/1.0'})
    resp.raise_for_status()
    return resp.text


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MCP-сервер каталога buddyooo.ru')
    parser.add_argument('--http', action='store_true',
                        help='streamable-http на %s:%d (путь /mcp) вместо stdio' % (HOST, PORT))
    args = parser.parse_args()
    if args.http:
        mcp.run(transport='streamable-http')
    else:
        mcp.run()  # stdio-транспорт по умолчанию
