import importlib.metadata
import logging
import optillm
from typing import Optional, Dict, Any
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptillmAdapter:
    """Adapter class to integrate optillm's optimisation capabilities into the Bedrock gateway"""

    def __init__(self, enabled: bool = False, approach: str = "auto"):
        self.enabled = enabled
        self.approach = approach
        self._optillm_imported = False
        self._optimisers = {}

        if enabled:
            try:
                # Verify optillm is installed
                importlib.metadata.version("optillm")
                self._import_optimisers()
                self._optillm_imported = True
            except importlib.metadata.PackageNotFoundError:
                raise ImportError(
                    "optillm package is not installed. Please install it with: pip install optillm"
                )

    def _import_optimisers(self):
        try:
            from optillm.mcts import chat_with_mcts
            from optillm.bon import best_of_n_sampling
            from optillm.moa import mixture_of_agents
            from optillm.rto import round_trip_optimization
            from optillm.pvg import inference_time_pv_game
            from optillm.z3_solver import Z3SymPySolverSystem
            from optillm.rstar import RStar
            from optillm.plansearch import plansearch
            from optillm.leap import leap
            from optillm.reread import re2_approach

            self._optimisers = {
                "mcts": chat_with_mcts,
                "bon": best_of_n_sampling,
                "moa": mixture_of_agents,
                "rto": round_trip_optimization,
                "pvg": inference_time_pv_game,
                "z3": Z3SymPySolverSystem().process_query,
                "rstar": RStar(None, None, None).solve,
                "plansearch": plansearch,
                "leap": leap,
                "re2": re2_approach
            }
        except ImportError as e:
            raise ImportError(f"Failed to import optillm modules: {str(e)}")

    async def optimise_request(
        self, messages: list, model: str, temperature: float = 0.7, **kwargs
    ) -> Dict[str, Any]:
        """
        Optimise the chat completion request using optillm if enabled

        Args:
            messages: List of chat messages
            model: Model identifier
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Dict containing the optimised request
        """
        if not self.enabled or not self._optillm_imported:
            logger.debug("Optillm optimisation skipped - not enabled or imported")
            return {
                "messages": messages,
                "model": model,
                "temperature": temperature,
                **kwargs,
            }

        try:
            # Extract system prompt and user messages
            system_prompt = ""
            conversation = []

            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    conversation.append(f"{msg['role'].capitalize()}: {msg['content']}")

            initial_query = "\n".join(conversation)

            # Get the appropriate optimiser
            optimiser = self._optimisers.get(self.approach)
            logger.info(f"Optimising request using {self.approach} approach")
            if not optimiser:
                raise ValueError(f"Unknown optimisation approach: {self.approach}")

            # Run optimisation
            optimised_content, _ = optimiser(
                system_prompt=system_prompt,
                initial_query=initial_query,
                model=model,
                temperature=temperature,
            )

            logger.info("Optimisation complete")

            # Return optimised request
            return {
                "messages": [{"role": "assistant", "content": optimised_content}],
                "model": model,
                "temperature": temperature,
                **kwargs,
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Optimisation failed: {str(e)}"
            )
