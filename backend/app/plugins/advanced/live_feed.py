import asyncio
import logging
from app.plugins.base import OSINTPlugin, PluginResult
import httpx

logger = logging.getLogger(__name__)


class LiveFeedPlugin(OSINTPlugin):
    plugin_id = "live-feed"
    name = "Live Feed"
    category = "advanced"
    description = "Real-time cyber news, threat intel, dark web mentions"
    input_types = ["domain", "ip", "name"]
    icon = "📰"

    async def run(self, target: str) -> PluginResult:
        # Try to fetch live RSS news from The Hacker News
        news_items = []

        try:
            import feedparser
            feed = await asyncio.get_event_loop().run_in_executor(
                None, lambda: feedparser.parse("https://feeds.feedburner.com/TheHackersNews")
            )
            for entry in feed.entries[:8]:
                news_items.append({
                    "title": entry.get("title", "No title"),
                    "source": "The Hacker News",
                    "publishedAt": entry.get("published", "")[:10] if entry.get("published") else "",
                    "url": entry.get("link", ""),
                })
        except ImportError:
            logger.debug("feedparser library not available")
        except Exception as e:
            logger.debug("RSS feed fetch failed: %s", e)

        if not news_items:
            return PluginResult(
                plugin_id=self.plugin_id,
                plugin_name=self.name,
                category=self.category,
                target=target,
                gui_data={
                    "Target": target,
                    "Articles Found": 0,
                    "Status": "No news articles available",
                    "Note": "Live news feed requires internet access to RSS sources",
                },
                terminal_data=f"Live Feed — {target}\n---\nNo news articles available.\nLive news feed requires internet access to RSS sources.",
            )

        gui_data = {"Recent Articles": len(news_items)}
        for i, item in enumerate(news_items[:8]):
            gui_data[f"Article {i + 1}"] = f"{item['title']} — {item['source']} ({item['publishedAt']})"

        terminal_lines = [f"Live Feed — {target}", "---"]
        for item in news_items[:8]:
            terminal_lines.append(f"• [{item['publishedAt']}] {item['title']}")

        return PluginResult(
            plugin_id=self.plugin_id,
            plugin_name=self.name,
            category=self.category,
            target=target,
            gui_data=gui_data,
            terminal_data="\n".join(terminal_lines),
        )
