import httpx
import time
import logging
from typing import Optional, Tuple, Any


logger = logging.getLogger("indra.fetch")

PRIMARY_TIMEOUT  = 7.0
FALLBACK_TIMEOUT = 6.0


async def safe_fetch(
    primary_url:    str,
    fallback_url:   Optional[str] = None,
    primary_label:  str = "primary",
    fallback_label: str = "fallback",
    headers:        Optional[dict] = None,
    params:         Optional[dict] = None,
) -> Tuple[Optional[Any], str, bool, int]:
    """
    Fetch JSON from primary_url with automatic fallback.

    Returns:
        (data, source_label, is_fallback, response_ms)
        data is None if both primary and fallback fail.
    """
    start = time.monotonic()

    # ── Primary attempt ───────────────────────────────────────────
    try:
        async with httpx.AsyncClient(
            timeout=PRIMARY_TIMEOUT,
            follow_redirects=True,
        ) as client:
            resp = await client.get(
                primary_url,
                headers=headers or {},
                params=params or {},
            )
            resp.raise_for_status()
            ms = int((time.monotonic() - start) * 1000)
            logger.info(
                f"[OK] {primary_label} → {resp.status_code} in {ms}ms"
            )
            return resp.json(), primary_label, False, ms

    except httpx.TimeoutException:
        logger.warning(
            f"[TIMEOUT] {primary_label} exceeded {PRIMARY_TIMEOUT}s"
        )
    except httpx.HTTPStatusError as e:
        logger.warning(
            f"[HTTP {e.response.status_code}] {primary_label} "
            f"returned error status"
        )
    except Exception as e:
        logger.warning(
            f"[ERROR] {primary_label}: {type(e).__name__}: {e}"
        )

    # ── Fallback attempt ──────────────────────────────────────────
    if fallback_url:
        try:
            async with httpx.AsyncClient(
                timeout=FALLBACK_TIMEOUT,
                follow_redirects=True,
            ) as client:
                resp = await client.get(
                    fallback_url,
                    headers=headers or {},
                    params=params or {},
                )
                resp.raise_for_status()
                ms = int((time.monotonic() - start) * 1000)
                logger.info(
                    f"[FALLBACK OK] {fallback_label} in {ms}ms"
                )
                return resp.json(), fallback_label, True, ms

        except httpx.TimeoutException:
            logger.error(
                f"[FALLBACK TIMEOUT] {fallback_label} "
                f"exceeded {FALLBACK_TIMEOUT}s"
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"[FALLBACK HTTP {e.response.status_code}] "
                f"{fallback_label}"
            )
        except Exception as e:
            logger.error(
                f"[FALLBACK ERROR] {fallback_label}: "
                f"{type(e).__name__}: {e}"
            )

    # ── Both failed ───────────────────────────────────────────────
    ms = int((time.monotonic() - start) * 1000)
    logger.error(
        f"[TOTAL FAIL] Both {primary_label} and fallback "
        f"unreachable after {ms}ms"
    )
    return None, "none", False, ms


async def safe_fetch_xml(
    url:     str,
    label:   str = "rss",
    headers: Optional[dict] = None,
) -> Tuple[Optional[str], int]:
    """
    Fetch raw XML/RSS text.
    Returns (text_content, response_ms).
    text_content is None if the request failed.
    """
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(
            timeout=PRIMARY_TIMEOUT,
            follow_redirects=True,
        ) as client:
            resp = await client.get(
                url,
                headers=headers or {},
            )
            resp.raise_for_status()
            ms = int((time.monotonic() - start) * 1000)
            logger.info(f"[XML OK] {label} in {ms}ms")
            return resp.text, ms

    except httpx.TimeoutException:
        logger.warning(f"[XML TIMEOUT] {label}")
    except httpx.HTTPStatusError as e:
        logger.warning(
            f"[XML HTTP {e.response.status_code}] {label}"
        )
    except Exception as e:
        logger.warning(
            f"[XML ERROR] {label}: {type(e).__name__}: {e}"
        )

    ms = int((time.monotonic() - start) * 1000)
    return None, ms