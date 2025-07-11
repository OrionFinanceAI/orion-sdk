"""Utility functions for the Orion Python SDK."""

import random
import uuid

import numpy as np

from .contracts import OrionConfig

random.seed(uuid.uuid4().int)  # uuid-based random seed for irreproducibility.

# TODO: coprocessor, for encoded intents: to check FHE encrypted intents associated with protocol public FHE context.


def validate_order(order_intent: dict, fuzz: bool = False) -> dict:
    """Validate an order intent."""
    orion_config = OrionConfig()

    # Validate all tokens are whitelisted
    for token_address in order_intent.keys():
        if not orion_config.is_whitelisted(token_address):
            raise ValueError(f"Token {token_address} is not whitelisted")

    # Validate all amounts are positive
    if any(weight <= 0 for weight in order_intent.values()):
        raise ValueError("All amounts must be positive")

    # Validate the sum of amounts is approximately 1 (within tolerance for floating point error)
    TOLERANCE = 1e-10
    if not np.isclose(sum(order_intent.values()), 1, atol=TOLERANCE):
        raise ValueError(
            "The sum of amounts is not 1 (within floating point tolerance)."
        )

    curator_intent_decimals = orion_config.curator_intent_decimals

    if fuzz:
        # Add remaining whitelisted assets with small random amounts
        for asset in orion_config.whitelisted_assets:
            if asset not in order_intent.keys():
                order_intent[asset] = (
                    random.randint(1, 10) / 10**curator_intent_decimals
                )

        # Normalize again to sum to 1
        order_intent = {
            token: weight / sum(order_intent.values())
            for token, weight in order_intent.items()
        }

    order_intent = {
        token: weight * 10**curator_intent_decimals
        for token, weight in order_intent.items()
    }
    rounded_values = round_with_fixed_sum(
        list(order_intent.values()), 10**curator_intent_decimals
    )
    order_intent = dict(zip(order_intent.keys(), rounded_values))

    return order_intent


def round_with_fixed_sum(
    values: list[float], target_sum: int | None = None
) -> list[int]:
    """Round a list of values to a fixed sum."""
    values = np.asarray(values, dtype=np.float64)

    if target_sum is None:
        target_sum = int(round(np.sum(values)))

    floored = np.floor(values).astype(int)
    remainder = int(round(target_sum - np.sum(floored)))

    # Get the fractional parts and their indices
    fractional_parts = values - floored
    indices = np.argsort(-fractional_parts)  # Descending order

    # Allocate the remaining units
    result = floored.copy()
    result[indices[:remainder]] += 1

    return result.tolist()
