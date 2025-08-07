"""Billing module for charging token usage in the Apify Actor."""

import math
from apify import Actor


async def charge_tokens(input_tokens: int, output_tokens: int) -> None:
    """
    Charge for token usage based on the pay-per-event pricing model.
    
    Args:
        input_tokens (int): Number of input tokens consumed
        output_tokens (int): Number of output tokens generated
    """
    try:
        # Calculate number of 100-token blocks for input and output tokens
        input_blocks = math.ceil(input_tokens / 100) if input_tokens > 0 else 0
        output_blocks = math.ceil(output_tokens / 100) if output_tokens > 0 else 0
        
        Actor.log.info(f"Charging for {input_tokens} input tokens ({input_blocks} blocks)")
        Actor.log.info(f"Charging for {output_tokens} output tokens ({output_blocks} blocks)")
        
        # Charge for input tokens if any
        if input_blocks > 0:
            await Actor.charge("gpt-4-1-mini-input-tokens-100", input_blocks)
        
        # Charge for output tokens if any
        if output_blocks > 0:
            await Actor.charge("gpt-4-1-mini-output-tokens-100", output_blocks)
            
    except Exception as e:
        Actor.log.error(f"Failed to charge tokens: {e}")
        raise
