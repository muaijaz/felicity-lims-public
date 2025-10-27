import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict

import httpx
from fastapi import APIRouter, HTTPException
from packaging import version

__version__ = "0.2.1"

_cache_duration = timedelta(hours=1)
router = APIRouter()


class FelicityVersion:
    _version = __version__
    _owner = "aurthurm"  # beak-insights
    _repo = "felicity-lims"
    _pat = os.getenv("GITHUB_TOKEN", None)  # Optional GitHub token from environment
    _cache = {}
    _cache_duration = _cache_duration
    _last_check = None
    _lock = asyncio.Lock()

    @property
    def version(self) -> str:
        return self._version

    async def _fetch_github_version(self) -> Dict:
        url = f"https://api.github.com/repos/{self._owner}/{self._repo}/releases/latest"
        headers = {"Accept": "application/vnd.github.v3+json"}

        # Only add auth if token is available
        if self._pat:
            headers["Authorization"] = f"Bearer {self._pat}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                raise HTTPException(status_code=504, detail="GitHub API request timed out")
            except httpx.HTTPError as e:
                if e.response and e.response.status_code == 403:
                    raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded")
                if e.response and e.response.status_code == 401:
                    raise HTTPException(status_code=503, detail="Version check unavailable (GitHub auth required)")
                raise HTTPException(status_code=502, detail=f"GitHub API error: {str(e)}")

    async def check_github_version(self) -> Dict:
        async with self._lock:
            now = datetime.now()

            # Return cached response if valid
            if self._last_check and (now - self._last_check) < self._cache_duration:
                return self._cache

            latest_release = await self._fetch_github_version()
            latest_version = latest_release["tag_name"].lstrip("v")

            try:
                current = version.parse(self.version)
                latest = version.parse(latest_version)
            except version.InvalidVersion as e:
                raise HTTPException(status_code=500, detail=f"Invalid version format: {str(e)}")

            result = {
                "current_version": str(current),
                "latest_version": str(latest),
                "update_available": latest > current,
                "release_notes": latest_release.get("body", ""),
                "release_url": latest_release["html_url"],
                "last_checked": now.isoformat()
            }

            # Update cache
            self._cache = result
            self._last_check = now

            return result


# use as singleton
felicity_version = FelicityVersion()
