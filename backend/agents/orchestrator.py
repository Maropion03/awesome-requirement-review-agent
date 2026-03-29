"""
Orchestrator Agent - coordinates review agents.
"""

import os
from typing import Optional

from crewai import Agent, Crew

from utils.minimax_client import get_minimax_client
from config.prompts import ORCHESTRATOR_PROMPT


class Orchestrator:
    """Main orchestrator agent for PRD review."""

    def __init__(
        self,
        model: str = "MiniMax-M2.7",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.llm = get_minimax_client(
            model=model,
            api_key=api_key,
            api_base=api_base,
            streaming=True,
        )

        self.agent = Agent(
            role="评审协调者",
            goal="协调各评审 Agent，高效完成 PRD 评审任务",
            backstory=ORCHESTRATOR_PROMPT,
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
        )

    def get_agent(self) -> Agent:
        """Get the underlying CrewAI Agent."""
        return self.agent
