import asyncio
import logging
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import httpx
from app.models.schemas import SearchRequest, SearchResponse, PluginResultData
from app.services.orchestrator import OrchestratorService
from app.core.detector import AutoDetect
from app.core.sanitizer import sanitize_target, validate_target, InputValidationError
from app.core.api_key_auth import require_api_key

logger = logging.getLogger("trinetra.target_intel")

router = APIRouter(prefix="/api", tags=["search"])
orchestrator = OrchestratorService()


@router.get("/target-intel")
async def target_intel(target: str, _key: str = Depends(require_api_key)):
    """Fetch target-specific web intelligence.
    
    Searches the web for information about the given target using
    DuckDuckGo's free Instant Answer API and filters local RSS news
    for relevant mentions.
    """
    try:
        target = sanitize_target(target)
    except InputValidationError as e:
        raise HTTPException(400, detail={"error": e.message, "detail": e.detail})

    target_type = AutoDetect.detect(target)
    web_results = []
    news_results = []
    related_info = {}

    async def search_duckduckgo():
        """Search DuckDuckGo Instant Answer API (free, no key)."""
        nonlocal web_results, related_info
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # DuckDuckGo Instant Answer API
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": target,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1,
                    },
                    headers={"User-Agent": "TRINETRA-OSINT/1.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    abstract = data.get("AbstractText", "")
                    abstract_source = data.get("AbstractSource", "")
                    abstract_url = data.get("AbstractURL", "")
                    
                    if abstract:
                        web_results.append({
                            "title": f"Wikipedia / {abstract_source}" if abstract_source else "Summary",
                            "snippet": abstract[:500],
                            "url": abstract_url,
                            "source": abstract_source or "DuckDuckGo",
                            "type": "abstract",
                        })
                        related_info["abstract"] = abstract[:500]
                        related_info["source"] = abstract_source
                        related_info["url"] = abstract_url

                    # Related topics
                    related = data.get("RelatedTopics", [])
                    for topic in related[:8]:
                        if "Text" in topic and "FirstURL" in topic:
                            web_results.append({
                                "title": topic.get("Text", "").split(" - ")[0][:100],
                                "snippet": topic.get("Text", "")[:300],
                                "url": topic.get("FirstURL", ""),
                                "source": topic.get("Icon", {}).get("URL", "DuckDuckGo") or "DuckDuckGo",
                                "type": "related",
                            })
                        elif "Topics" in topic:
                            for sub in topic["Topics"][:4]:
                                if "Text" in sub and "FirstURL" in sub:
                                    web_results.append({
                                        "title": sub.get("Text", "").split(" - ")[0][:100],
                                        "snippet": sub.get("Text", "")[:300],
                                        "url": sub.get("FirstURL", ""),
                                        "source": "DuckDuckGo",
                                        "type": "related",
                                    })

                    # Results from the web
                    results = data.get("Results", [])
                    for r in results[:5]:
                        if "Text" in r and "FirstURL" in r:
                            web_results.append({
                                "title": r.get("Text", "").split(" - ")[0][:100],
                                "snippet": r.get("Text", "")[:300],
                                "url": r.get("FirstURL", ""),
                                "source": r.get("Source", "Web"),
                                "type": "result",
                            })

        except Exception as e:
            logger.debug("DuckDuckGo search failed for %s: %s", target, e)

    async def search_news():
        """Search local RSS news cache for target mentions."""
        nonlocal news_results
        try:
            from app.services.real_news_service import real_news_service
            headlines = real_news_service.get_latest(100)
            target_lower = target.lower()
            for item in headlines:
                text = (item.get("text", "") + " " + item.get("source", "")).lower()
                keywords = target_lower.split(".") if "." in target_lower else [target_lower]
                if any(kw in text for kw in keywords if len(kw) > 2):
                    news_results.append(item)
            # Limit to top 10 matches
            news_results[:] = news_results[:10]
        except Exception as e:
            logger.debug("News search failed for %s: %s", target, e)

    # Run both searches in parallel
    await asyncio.gather(search_duckduckgo(), search_news(), return_exceptions=True)

    detected_type = AutoDetect.detect_full(target) if target_type != "unknown" else {
        "target": target,
        "detected_type": "unknown",
        "confidence": 0,
    }

    return {
        "target": target,
        "target_type": target_type,
        "detected": detected_type,
        "web_results": web_results[:15],
        "news_mentions": news_results,
        "related_info": related_info,
        "total_web": len(web_results),
        "total_news": len(news_results),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/search")
async def search(request: SearchRequest, _key: str = Depends(require_api_key)):
    """Run all applicable OSINT plugins against a target."""
    # Sanitize input
    try:
        target = sanitize_target(request.target)
    except InputValidationError as e:
        raise HTTPException(400, detail={"error": e.message, "detail": e.detail})

    # Validate target type
    is_valid, detected_type, validation_error = validate_target(target)
    if not is_valid and not request.type:
        raise HTTPException(400, detail={"error": validation_error})

    # Auto-detect type
    target_type = request.type or detected_type
    if target_type == "unknown":
        target_type = "domain"  # default fallback

    # Run all matching plugins in parallel
    results = await orchestrator.run_all(target, target_type)

    return SearchResponse(
        target=target,
        type=target_type,
        timestamp=datetime.now(timezone.utc),
        total_plugins=len(results),
        completed_plugins=sum(1 for r in results if r.get("status") == "completed"),
        results=results,
    )


@router.get("/search/{target}")
async def search_get(target: str, _key: str = Depends(require_api_key)):
    """GET version of search for simple lookups."""
    # Sanitize input
    try:
        target = sanitize_target(target)
    except InputValidationError as e:
        raise HTTPException(400, detail={"error": e.message, "detail": e.detail})

    target_type = AutoDetect.detect(target)
    if target_type == "unknown":
        target_type = "domain"

    results = await orchestrator.run_all(target, target_type)

    return SearchResponse(
        target=target,
        type=target_type,
        timestamp=datetime.now(timezone.utc),
        total_plugins=len(results),
        completed_plugins=sum(1 for r in results if r.get("status") == "completed"),
        results=results,
    )


@router.get("/detect")
async def detect_target(target: str, _key: str = Depends(require_api_key)):
    """Auto-detect what type of target this is."""
    try:
        target = sanitize_target(target)
    except InputValidationError as e:
        raise HTTPException(400, detail={"error": e.message, "detail": e.detail})
    return AutoDetect.detect_full(target)


@router.get("/plugins")
async def list_plugins(_key: str = Depends(require_api_key)):
    """List all available OSINT plugins."""
    from app.plugins.registry import plugin_registry
    return {
        "total": len(plugin_registry.plugins),
        "plugins": [
            {
                "id": p.plugin_id,
                "name": p.name,
                "category": p.category,
                "description": p.description,
                "input_types": p.input_types,
            }
            for p in plugin_registry.plugins
        ],
    }
