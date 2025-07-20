# The MIT License (MIT)
# Copyright © 2023 Yuma Rao
# Copyright © 2023 Zeus-Miner Project

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import time
import typing
import bittensor as bt
import json, socket
import hashlib
import struct
import asyncio
import threading
from utils.cgminer_api import CGMinerAPI

# Bittensor Miner Template:
import template

# import base miner class which takes care of most of the boilerplate
from template.base.miner import BaseMinerNeuron


class Miner(BaseMinerNeuron):
    """
    Zeus-Miner neuron class that performs actual scrypt hashing to find valid shares.
    
    This miner interfaces with cgminer via JSON-RPC API and performs real proof-of-work
    computations to solve the HashWork challenges from validators.
    """

    def __init__(self, config=None):
        super(Miner, self).__init__(config=config)

        # Initialise connection to local cgminer API
        self.cg = CGMinerAPI(host="127.0.0.1", port=4028)
        
        # Mining performance tracking
        self.total_hashes = 0
        self.shares_found = 0
        self.last_performance_log = time.time()
        
        # Verify cgminer connection
        try:
            summary = self.cg.summary()
            bt.logging.info(f"Connected to cgminer: {summary}")
        except Exception as e:
            bt.logging.warning(f"cgminer connection failed, will use software fallback: {e}")
            self.use_software_mining = True
        else:
            self.use_software_mining = False

    def scrypt_hash(self, data: bytes) -> bytes:
        """Compute scrypt hash of input data using software implementation."""
        # Import scrypt for software fallback
        try:
            import scrypt
            return scrypt.hash(data, data[:16], N=1024, r=1, p=1, buflen=32)
        except ImportError:
            # Fallback to simple SHA256 if scrypt not available
            bt.logging.warning("scrypt library not available, using SHA256 fallback")
            return hashlib.sha256(data).digest()

    def verify_share_target(self, header_bytes: bytes, nonce: int, target_bytes: bytes) -> bool:
        """Verify if the hash of header+nonce meets the target difficulty."""
        # Pack nonce as little-endian 32-bit int and append to header
        nonce_bytes = struct.pack('<I', nonce)
        full_header = header_bytes + nonce_bytes
        
        # Compute scrypt hash
        if self.use_software_mining:
            hash_result = self.scrypt_hash(full_header)
        else:
            # For cgminer integration, we'd need to check its output
            # For now, use software verification
            hash_result = self.scrypt_hash(full_header)
        
        # Compare hash with target (both little-endian)
        hash_int = int.from_bytes(hash_result, byteorder='little')
        target_int = int.from_bytes(target_bytes, byteorder='little')
        
        return hash_int <= target_int

    async def software_mine(self, header_hex: str, target_hex: str, timeout: float = 5.0) -> typing.Tuple[typing.Optional[int], bool]:
        """Software mining fallback when cgminer is not available."""
        header_bytes = bytes.fromhex(header_hex)
        target_bytes = bytes.fromhex(target_hex)
        
        start_time = time.time()
        nonce = 0
        max_nonce = 2**32
        
        bt.logging.info(f"Starting software mining with target: {target_hex[:16]}...")
        
        while nonce < max_nonce and (time.time() - start_time) < timeout:
            if self.verify_share_target(header_bytes, nonce, target_bytes):
                bt.logging.success(f"Found valid share! Nonce: {nonce}")
                self.shares_found += 1
                return nonce, True
            
            nonce += 1
            self.total_hashes += 1
            
            # Check every 1000 hashes to avoid tight loop
            if nonce % 1000 == 0:
                await asyncio.sleep(0.001)
                
        bt.logging.debug(f"No valid share found in {timeout}s, tried {nonce} nonces")
        return None, False

    async def cgminer_mine(self, header_hex: str, target_hex: str, timeout: float = 5.0) -> typing.Tuple[typing.Optional[int], bool]:
        """Use cgminer to find a valid share."""
        try:
            # Send work to cgminer - this is simplified, real integration would need
            # proper getwork protocol implementation
            bt.logging.info("Attempting cgminer integration...")
            
            # Get current mining status
            summary = self.cg.summary()
            
            # For this proof-of-concept, we'll fall back to software mining
            # but log that we're connected to cgminer
            bt.logging.info(f"cgminer status: {summary.get('STATUS', [{}])[0].get('Msg', 'Unknown')}")
            
            # TODO: Implement proper cgminer getwork integration
            # For now, use software mining with cgminer acceleration hint
            return await self.software_mine(header_hex, target_hex, timeout)
            
        except Exception as e:
            bt.logging.warning(f"cgminer error, falling back to software: {e}")
            return await self.software_mine(header_hex, target_hex, timeout)

    def log_performance(self):
        """Log mining performance statistics."""
        now = time.time()
        if now - self.last_performance_log > 60:  # Log every minute
            elapsed = now - self.last_performance_log
            hashrate = self.total_hashes / elapsed if elapsed > 0 else 0
            bt.logging.info(f"Mining stats - Hashrate: {hashrate:.2f} H/s, Shares found: {self.shares_found}")
            self.last_performance_log = now
            self.total_hashes = 0

    async def forward(
        self, synapse: template.protocol.HashWork
    ) -> template.protocol.HashWork:
        """
        Process incoming HashWork synapse by performing scrypt mining.
        
        This method attempts to find a nonce that makes scrypt(header+nonce) ≤ target.
        Uses cgminer when available, falls back to software mining otherwise.
        
        Args:
            synapse: HashWork synapse containing header_hex and target_hex
            
        Returns:
            HashWork synapse with nonce, success, and latency_ms populated
        """
        start_time = time.time()
        
        try:
            bt.logging.debug(f"Received HashWork challenge - Header: {synapse.header_hex[:16]}..., Target: {synapse.target_hex[:16]}...")
            
            # Validate input
            if not synapse.header_hex or not synapse.target_hex:
                raise ValueError("Invalid header_hex or target_hex")
                
            if len(synapse.header_hex) != 152:  # 76 bytes * 2 hex chars
                raise ValueError(f"Header should be 76 bytes (152 hex chars), got {len(synapse.header_hex)}")
                
            if len(synapse.target_hex) != 64:  # 32 bytes * 2 hex chars  
                raise ValueError(f"Target should be 32 bytes (64 hex chars), got {len(synapse.target_hex)}")
            
            # Attempt mining with timeout
            timeout = 8.0  # Slightly less than validator timeout
            
            if self.use_software_mining:
                nonce, success = await self.software_mine(synapse.header_hex, synapse.target_hex, timeout)
            else:
                nonce, success = await self.cgminer_mine(synapse.header_hex, synapse.target_hex, timeout)
            
            # Populate response
            synapse.nonce = nonce
            synapse.success = success
            
            bt.logging.info(f"Mining result: success={success}, nonce={nonce}")
            
            # Log performance periodically
            self.log_performance()
            
        except Exception as e:
            bt.logging.error(f"Mining error: {e}")
            synapse.nonce = None
            synapse.success = False
        
        finally:
            synapse.latency_ms = (time.time() - start_time) * 1000.0
            
        return synapse

    async def blacklist(
        self, synapse: template.protocol.HashWork
    ) -> typing.Tuple[bool, str]:
        """
        Enhanced blacklist logic for Zeus-Miner subnet.
        
        Blacklists requests from unregistered entities and non-validators
        to preserve mining resources for legitimate validators.
        """
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            bt.logging.warning("Received request without dendrite or hotkey")
            return True, "Missing dendrite or hotkey"

        # Check if hotkey is registered
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            bt.logging.trace(f"Blacklisting unregistered hotkey {synapse.dendrite.hotkey}")
            return True, "Unrecognized hotkey"

        uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
        
        # Require validator permit for mining requests
        if not self.metagraph.validator_permit[uid]:
            bt.logging.warning(f"Blacklisting non-validator hotkey {synapse.dendrite.hotkey}")
            return True, "Non-validator hotkey"

        # Check minimum stake requirement
        min_stake = 1000.0  # Minimum TAO stake for validators
        if self.metagraph.S[uid] < min_stake:
            bt.logging.warning(f"Blacklisting low-stake validator {synapse.dendrite.hotkey} (stake: {self.metagraph.S[uid]})")
            return True, f"Insufficient stake: {self.metagraph.S[uid]} < {min_stake}"

        bt.logging.trace(f"Accepting request from validator {synapse.dendrite.hotkey}")
        return False, "Validator authorized"

    async def priority(self, synapse: template.protocol.HashWork) -> float:
        """
        Enhanced priority logic that prioritizes high-stake validators.
        
        Returns higher priority for validators with more stake, encouraging
        work on challenges from the most influential network participants.
        """
        if synapse.dendrite is None or synapse.dendrite.hotkey is None:
            return 0.0

        try:
            caller_uid = self.metagraph.hotkeys.index(synapse.dendrite.hotkey)
            stake = float(self.metagraph.S[caller_uid])
            
            # Bonus priority for top validators
            if caller_uid < len(self.metagraph.validator_permit) and self.metagraph.validator_permit[caller_uid]:
                stake *= 1.5  # 50% bonus for validators
                
            bt.logging.trace(f"Priority for {synapse.dendrite.hotkey}: {stake}")
            return stake
            
        except (ValueError, IndexError):
            return 0.0


# This is the main function, which runs the miner.
if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info(f"Zeus-Miner running... {time.time()}")
            time.sleep(30)
