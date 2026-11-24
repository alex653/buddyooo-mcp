# Buddyooo MCP Server

Open Model Context Protocol (MCP) server for the [buddyooo.ru](https://buddyooo.ru) catalog —
a Russian e-commerce store of electrical equipment (82,000+ products, 616 brands: IEK, TOKOV ELECTRIC, KARAT, Dekraft, etc.).

**Public URL — no registration, no API keys:**

```
https://mcp.buddyooo.ru/mcp
```

Neural-network search understands natural-language queries: "автомат на 16 ампер",
"кабель для прокладки в земле". Prices and stock update daily from the supplier feed.

## Connect

### Remote (recommended — works in Claude Code, Claude Desktop, Cursor, Windsurf, etc.)

```json
{
  "mcpServers": {
    "buddyooo": {
      "url": "https://mcp.buddyooo.ru/mcp"
    }
  }
}
```

Claude Code one-liner:

```bash
claude mcp add --transport http buddyooo https://mcp.buddyooo.ru/mcp
```

### Local stdio

```bash
pip install "mcp>=1.0,<2" httpx
python3 mcp_server.py
```

```json
{
  "mcpServers": {
    "buddyooo": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `search_products(query, limit)` | Neural search across the catalog: name, price (RUB), stock, alias, article, brand |
| `get_product(alias)` | Product card: price, stock, up to 50 specs, cleaned description, page URL |
| `list_categories(limit)` | Top catalog categories with product counts |
| resource `llms://full` | Full store reference: order/payment/delivery terms, contacts |

### Python example

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async with streamablehttp_client("https://mcp.buddyooo.ru/mcp") as (r, w, _):
    async with ClientSession(r, w) as s:
        await s.initialize()
        res = await s.call_tool("search_products",
                                {"query": "автомат 16 ампер", "limit": 5})
        print(res.content[0].text)
```

## REST API (no MCP needed)

- `GET https://buddyooo.ru/api/search?q=автомат+16+ампер&limit=5`
- `GET https://buddyooo.ru/api/product-info/<alias>`
- `GET https://buddyooo.ru/api/categories?limit=50`
- [`llms.txt`](https://buddyooo.ru/llms.txt) / [`llms-full.txt`](https://buddyooo.ru/llms-full.txt) — machine-readable store reference

## Rate limits

10 requests/sec per source IP (burst 20), HTTP 429 on excess. Repeated identical
queries are cached server-side for 5 minutes. Data refreshes nightly.

Attribution link to buddyooo.ru when using the data in assistant answers is appreciated.

---

## Русская версия

Открытый MCP-сервер каталога [buddyooo.ru](https://buddyooo.ru) — интернет-магазин
электротехнической продукции (82 000+ товаров, 616 брендов).

Подключение одной строкой, без регистрации:

```json
{ "mcpServers": { "buddyooo": { "url": "https://mcp.buddyooo.ru/mcp" } } }
```

- `search_products` — нейросетевой поиск «обычным языком» (цены, наличие)
- `get_product` — карточка товара с характеристиками
- `list_categories` — топ категорий каталога

Инструкции и REST API: https://buddyooo.ru/mcp · Машиночитаемая справка: [llms-full.txt](https://buddyooo.ru/llms-full.txt)

## License

[MIT](LICENSE) © BUDDY LLC (ООО «БАДДИ»)
