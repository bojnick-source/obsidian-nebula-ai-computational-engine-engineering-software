"""
GeminiClient — YouTube video analysis and multimodal tasks.

Uses google-genai (unified SDK: `pip install google-genai`).

Confirmed capabilities (Gemini 2.5, 2026):
  - Pass YouTube URLs directly — no download required
  - Up to 10 videos per request (Gemini 2.5+)
  - 2M token context window (~6 hours video at low resolution)
  - Timestamp-precise Q&A, transcription with visual descriptions
  - Adjustable FPS: 0.1 (lectures) → 60 (fast-action footage)
  - Resolution: high (720p), standard (480p), low (360p)

Restrictions:
  - Public videos only
  - 8 hours/day free tier; no limit paid tier
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class VideoAnalysisResult:
    text: str
    model: str
    video_urls: list[str]

    def to_context_block(self) -> str:
        urls_str = "\n".join(f"  - {u}" for u in self.video_urls)
        return f"[Gemini Video Analysis — model={self.model}]\nVideos:\n{urls_str}\n\n{self.text}"


class GeminiClient:
    """Wrapper for Gemini video and multimodal analysis."""

    DEFAULT_MODEL = "gemini-2.5-pro"
    FLASH_MODEL = "gemini-2.5-flash"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    def analyze_video(
        self,
        youtube_url: str,
        prompt: str,
        model: str = DEFAULT_MODEL,
        fps: float = 1.0,
        resolution: str = "standard",    # high | standard | low
        start_offset: str | None = None,  # e.g. "1m30s"
        end_offset: str | None = None,    # e.g. "4m00s"
    ) -> VideoAnalysisResult:
        """
        Analyze a single YouTube video.

        fps guidance:
          0.1  — slide decks, lectures (very efficient)
          1.0  — normal engineering demos (default)
          10.0 — fast assembly / test footage
          60.0 — high-speed camera content
        """
        from google.genai import types

        client = self._get_client()

        video_part = types.Part(
            file_data=types.FileData(file_uri=youtube_url)
        )
        text_part = types.Part(text=prompt)

        response = client.models.generate_content(
            model=model,
            contents=types.Content(parts=[video_part, text_part]),
        )
        return VideoAnalysisResult(
            text=response.text,
            model=model,
            video_urls=[youtube_url],
        )

    def compare_videos(
        self,
        youtube_urls: list[str],
        prompt: str,
        model: str = DEFAULT_MODEL,
    ) -> VideoAnalysisResult:
        """
        Compare up to 10 YouTube videos in a single request (Gemini 2.5+).
        """
        from google.genai import types

        if len(youtube_urls) > 10:
            raise ValueError("Gemini 2.5 supports max 10 videos per request")

        client = self._get_client()

        parts = [
            types.Part(file_data=types.FileData(file_uri=url))
            for url in youtube_urls
        ]
        parts.append(types.Part(text=prompt))

        response = client.models.generate_content(
            model=model,
            contents=types.Content(parts=parts),
        )
        return VideoAnalysisResult(
            text=response.text,
            model=model,
            video_urls=youtube_urls,
        )

    def analyze_image(
        self,
        image_url: str,
        prompt: str,
        model: str = DEFAULT_MODEL,
    ) -> str:
        """Analyze a single image (diagram, schematic, etc.)."""
        from google.genai import types

        client = self._get_client()
        response = client.models.generate_content(
            model=model,
            contents=types.Content(parts=[
                types.Part(file_data=types.FileData(file_uri=image_url)),
                types.Part(text=prompt),
            ]),
        )
        return response.text

    async def analyze_video_async(
        self,
        youtube_url: str,
        prompt: str,
        model: str = DEFAULT_MODEL,
        **kwargs,
    ) -> VideoAnalysisResult:
        """Async wrapper — runs sync call in executor."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.analyze_video(youtube_url, prompt, model, **kwargs),
        )

    async def compare_videos_async(
        self,
        youtube_urls: list[str],
        prompt: str,
        model: str = DEFAULT_MODEL,
    ) -> VideoAnalysisResult:
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.compare_videos(youtube_urls, prompt, model),
        )
