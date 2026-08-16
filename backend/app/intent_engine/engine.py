"""
AI Operating System - Intent Engine Interface

This module defines the abstract contract that every Intent Engine
implementation (Gemini, OpenAI, Ollama, Rule-Based, etc.) must follow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.intent_engine.models import (
    IntentContext,
    ParsedIntent,
)


class IntentEngine(ABC):
    """
    Base interface for all Intent Engine implementations.

    An implementation is responsible for converting natural language
    into a structured ParsedIntent object.
    """

    @abstractmethod
    async def parse(
        self,
        text: str,
        context: IntentContext | None = None,
    ) -> ParsedIntent:
        """
        Parse a user's natural language request.

        Example:
            "Rename demo.txt to final.txt"

        Returns:
            ParsedIntent
        """
        raise NotImplementedError

    @abstractmethod
    async def classify(
        self,
        text: str,
    ) -> ParsedIntent:
        """
        Classify the user's intent.

        Example:
            Rename
            Delete
            Search
            Create Project
        """
        raise NotImplementedError

    @abstractmethod
    async def extract(
        self,
        text: str,
    ) -> ParsedIntent:
        """
        Extract entities from the user's request.

        Example:
            demo.txt
            Downloads
            report.pdf
        """
        raise NotImplementedError

    @abstractmethod
    async def validate(
        self,
        intent: ParsedIntent,
    ) -> ParsedIntent:
        """
        Validate the parsed intent.

        This may detect missing information or ambiguities.
        """
        raise NotImplementedError

    @abstractmethod
    async def normalize(
        self,
        intent: ParsedIntent,
    ) -> ParsedIntent:
        """
        Normalize the parsed intent.

        Examples:
            Downloads -> C:/Users/Abhishek/Downloads
            pdf -> .pdf
        """
        raise NotImplementedError

    @abstractmethod
    async def resolve(
        self,
        intent: ParsedIntent,
    ) -> ParsedIntent:
        """
        Resolve the final intent before passing it to the Planner.
        """
        raise NotImplementedError