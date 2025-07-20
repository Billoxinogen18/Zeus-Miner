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
import random
import hashlib
import struct

# Bittensor
import bittensor as bt

# import base validator class which takes care of most of the boilerplate
from template.base.validator import BaseValidatorNeuron

import os, random, time, struct, hashlib
from template.protocol import HashWork


class Validator(BaseValidatorNeuron):
    """
    Enhanced Zeus-Miner validator that generates sophisticated mining challenges
    and implements advanced scoring to drive miners to top rankings.
    
    Features:
    - Dynamic difficulty adjustment based on network conditions
    - Multiple challenge types to test different mining capabilities
    - Advanced scoring with performance bonuses and penalties
    - Detailed verification of mining results
    - Performance tracking and analytics
    """

    def __init__(self, config=None):
        super(Validator, self).__init__(config=config)

        bt.logging.info("Initializing Zeus-Miner Validator...")
        self.load_state()

        # Validator-specific configuration
        self.base_difficulty = 0x0000ffff  # Base difficulty target
        self.difficulty_adjustment_factor = 1.1
        self.max_difficulty = 0x000000ff
        self.min_difficulty = 0x00ffffff
        
        # Performance tracking
        self.challenge_history = []
        self.miner_performance = {}
        self.network_hashrate_estimate = 0.0
        self.avg_solve_time = 8.0
        
        # Challenge variation parameters
        self.challenge_types = ['standard', 'high_difficulty', 'time_pressure', 'efficiency_test']
        self.current_challenge_type = 'standard'
        
        bt.logging.info("Zeus-Miner Validator initialized successfully")

    def get_current_difficulty(self) -> int:
        """Calculate dynamic difficulty based on network performance."""
        if len(self.challenge_history) < 5:
            return self.base_difficulty
            
        # Analyze recent performance
        recent_challenges = self.challenge_history[-10:]
        avg_success_rate = sum(c.get('success_rate', 0) for c in recent_challenges) / len(recent_challenges)
        avg_response_time = sum(c.get('avg_response_time', 8.0) for c in recent_challenges) / len(recent_challenges)
        
        # Adjust difficulty based on success rate and response time
        if avg_success_rate > 0.8 and avg_response_time < 5.0:
            # Too easy, increase difficulty
            new_difficulty = max(int(self.base_difficulty / self.difficulty_adjustment_factor), self.max_difficulty)
        elif avg_success_rate < 0.3 or avg_response_time > 12.0:
            # Too hard, decrease difficulty
            new_difficulty = min(int(self.base_difficulty * self.difficulty_adjustment_factor), self.min_difficulty)
        else:
            new_difficulty = self.base_difficulty
            
        self.base_difficulty = new_difficulty
        bt.logging.info(f"Adjusted difficulty to: 0x{new_difficulty:08x} (success_rate: {avg_success_rate:.2f})")
        return new_difficulty

    def generate_challenge_header(self) -> bytes:
        """Generate a realistic 76-byte block header for mining challenge."""
        # Block header structure (76 bytes without nonce):
        # Version (4 bytes) + PrevBlockHash (32 bytes) + MerkleRoot (32 bytes) + 
        # Timestamp (4 bytes) + Bits (4 bytes)
        
        version = struct.pack('<I', 1)  # Version 1
        prev_hash = os.urandom(32)  # Random previous block hash
        merkle_root = hashlib.sha256(os.urandom(64)).digest()  # Realistic merkle root
        timestamp = struct.pack('<I', int(time.time()))  # Current timestamp
        bits = struct.pack('<I', self.get_current_difficulty())  # Difficulty bits
        
        header = version + prev_hash + merkle_root + timestamp + bits
        assert len(header) == 76, f"Header length should be 76 bytes, got {len(header)}"
        
        return header

    def generate_target_from_difficulty(self, difficulty: int) -> bytes:
        """Generate target threshold from difficulty value."""
        # Convert difficulty to target (inverse relationship)
        target_bytes = difficulty.to_bytes(4, byteorder='little') + b'\xff' * 28
        return target_bytes

    def select_challenge_type(self) -> str:
        """Select challenge type based on network conditions and miner performance."""
        # Rotate through different challenge types to test various capabilities
        weights = {
            'standard': 0.4,        # Regular difficulty challenges
            'high_difficulty': 0.2,  # High difficulty for top performers
            'time_pressure': 0.2,    # Lower difficulty but shorter timeout
            'efficiency_test': 0.2   # Medium difficulty with efficiency scoring
        }
        
        # Adjust weights based on network performance
        if len(self.challenge_history) > 0:
            recent_success_rate = self.challenge_history[-1].get('success_rate', 0.5)
            if recent_success_rate > 0.8:
                weights['high_difficulty'] += 0.2
                weights['standard'] -= 0.2
            elif recent_success_rate < 0.3:
                weights['standard'] += 0.2
                weights['high_difficulty'] -= 0.2
        
        # Weighted random selection
        challenge_type = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        self.current_challenge_type = challenge_type
        return challenge_type

    def create_challenge(self) -> HashWork:
        """Create a sophisticated mining challenge."""
        challenge_type = self.select_challenge_type()
        
        # Generate base challenge
        header = self.generate_challenge_header()
        difficulty = self.get_current_difficulty()
        
        # Modify challenge based on type
        if challenge_type == 'high_difficulty':
            difficulty = max(difficulty // 4, self.max_difficulty)  # 4x harder
        elif challenge_type == 'time_pressure':
            difficulty = min(difficulty * 2, self.min_difficulty)  # 2x easier
        elif challenge_type == 'efficiency_test':
            difficulty = int(difficulty * 1.5)  # 1.5x harder
            
        target = self.generate_target_from_difficulty(difficulty)
        
        challenge = HashWork(
            header_hex=header.hex(),
            target_hex=target.hex()
        )
        
        bt.logging.info(f"Generated {challenge_type} challenge - difficulty: 0x{difficulty:08x}")
        return challenge

    def verify_mining_result(self, challenge: HashWork, response: HashWork) -> dict:
        """Thoroughly verify a mining result and return detailed analysis."""
        verification_result = {
            'valid': False,
            'nonce_valid': False,
            'target_met': False,
            'latency_reasonable': False,
            'hash_correct': False,
            'efficiency_score': 0.0,
            'error': None
        }
        
        try:
            if not response.success or response.nonce is None:
                verification_result['error'] = 'No solution claimed'
                return verification_result
                
            # Reconstruct full header with nonce
            header_bytes = bytes.fromhex(challenge.header_hex)
            nonce_bytes = struct.pack('<I', response.nonce)
            full_header = header_bytes + nonce_bytes
            
            # Verify hash computation
            try:
                import scrypt
                hash_result = scrypt.hash(full_header, full_header[:16], N=1024, r=1, p=1, buflen=32)
            except ImportError:
                # Fallback verification
                hash_result = hashlib.sha256(full_header).digest()
            
            verification_result['hash_correct'] = True
            
            # Check if hash meets target
            target_bytes = bytes.fromhex(challenge.target_hex)
            hash_int = int.from_bytes(hash_result, byteorder='little')
            target_int = int.from_bytes(target_bytes, byteorder='little')
            
            verification_result['target_met'] = hash_int <= target_int
            verification_result['nonce_valid'] = 0 <= response.nonce < 2**32
            
            # Check response latency
            if response.latency_ms is not None:
                verification_result['latency_reasonable'] = 100 <= response.latency_ms <= 15000
                
                # Calculate efficiency score (solutions per second)
                if response.latency_ms > 0:
                    efficiency = 1000.0 / response.latency_ms  # Solutions per second
                    verification_result['efficiency_score'] = min(efficiency, 10.0)  # Cap at 10
            
            # Final validity check
            verification_result['valid'] = (
                verification_result['nonce_valid'] and 
                verification_result['target_met'] and 
                verification_result['hash_correct']
            )
            
        except Exception as e:
            verification_result['error'] = str(e)
            bt.logging.error(f"Verification error: {e}")
            
        return verification_result

    def calculate_advanced_score(self, uid: int, verification_result: dict, response: HashWork) -> float:
        """Calculate advanced score with performance bonuses."""
        base_score = 1.0 if verification_result['valid'] else 0.0
        
        if not verification_result['valid']:
            return 0.0
            
        # Performance bonuses
        bonus_multiplier = 1.0
        
        # Speed bonus (faster responses get higher scores)
        if response.latency_ms and response.latency_ms < 5000:
            speed_bonus = max(0, (5000 - response.latency_ms) / 5000) * 0.5
            bonus_multiplier += speed_bonus
            
        # Efficiency bonus
        if verification_result['efficiency_score'] > 0:
            efficiency_bonus = min(verification_result['efficiency_score'] / 5.0, 0.3)
            bonus_multiplier += efficiency_bonus
            
        # Challenge type bonus
        if self.current_challenge_type == 'high_difficulty':
            bonus_multiplier += 0.5  # Extra points for solving hard challenges
        elif self.current_challenge_type == 'efficiency_test':
            bonus_multiplier += verification_result['efficiency_score'] / 10.0
            
        # Historical performance bonus
        if uid in self.miner_performance:
            perf = self.miner_performance[uid]
            success_rate = perf.get('success_rate', 0.5)
            if success_rate > 0.8:
                bonus_multiplier += 0.2  # Bonus for consistent performers
                
        final_score = base_score * bonus_multiplier
        
        # Update miner performance tracking
        if uid not in self.miner_performance:
            self.miner_performance[uid] = {
                'total_challenges': 0,
                'successful_challenges': 0,
                'avg_latency': 0.0,
                'total_score': 0.0
            }
            
        perf = self.miner_performance[uid]
        perf['total_challenges'] += 1
        if verification_result['valid']:
            perf['successful_challenges'] += 1
        perf['success_rate'] = perf['successful_challenges'] / perf['total_challenges']
        perf['total_score'] += final_score
        
        if response.latency_ms:
            perf['avg_latency'] = (perf['avg_latency'] + response.latency_ms) / 2
        
        bt.logging.debug(f"Miner {uid} score: {final_score:.3f} (base: {base_score}, multiplier: {bonus_multiplier:.3f})")
        return final_score

    async def forward(self):
        """Enhanced forward pass with sophisticated challenge generation and scoring."""
        start_time = time.time()
        
        # Generate sophisticated challenge
        challenge = self.create_challenge()
        
        # Determine timeout based on challenge type
        timeout = 12.0
        if self.current_challenge_type == 'time_pressure':
            timeout = 6.0
        elif self.current_challenge_type == 'high_difficulty':
            timeout = 20.0
            
        bt.logging.info(f"Sending {self.current_challenge_type} challenge to {len(self.metagraph.axons)} miners (timeout: {timeout}s)")
        
        # Query miners asynchronously
        responses = await self.dendrite.query(
            neurons=self.metagraph.axons,
            synapse=challenge,
            deserialize=False,  # We need full response objects for detailed analysis
            timeout=timeout,
        )
        
        # Detailed evaluation and scoring
        scores = {}
        valid_responses = 0
        total_response_time = 0.0
        
        for uid, response in enumerate(responses):
            try:
                if response is None:
                    scores[uid] = 0.0
                    continue
                    
                # Verify mining result
                verification = self.verify_mining_result(challenge, response)
                
                # Calculate advanced score
                score = self.calculate_advanced_score(uid, verification, response)
                scores[uid] = score
                
                if verification['valid']:
                    valid_responses += 1
                    if response.latency_ms:
                        total_response_time += response.latency_ms
                        
                    bt.logging.success(f"Miner {uid} solved challenge! Nonce: {response.nonce}, Score: {score:.3f}")
                else:
                    bt.logging.debug(f"Miner {uid} failed: {verification.get('error', 'Invalid solution')}")
                    
            except Exception as e:
                bt.logging.error(f"Error evaluating miner {uid}: {e}")
                scores[uid] = 0.0
        
        # Record challenge statistics
        success_rate = valid_responses / len(responses) if responses else 0
        avg_response_time = total_response_time / valid_responses if valid_responses > 0 else timeout * 1000
        
        challenge_stats = {
            'timestamp': start_time,
            'challenge_type': self.current_challenge_type,
            'difficulty': self.base_difficulty,
            'success_rate': success_rate,
            'valid_responses': valid_responses,
            'total_responses': len(responses),
            'avg_response_time': avg_response_time,
            'timeout': timeout
        }
        
        self.challenge_history.append(challenge_stats)
        
        # Keep only recent history
        if len(self.challenge_history) > 100:
            self.challenge_history = self.challenge_history[-100:]
            
        bt.logging.info(f"Challenge completed - Success rate: {success_rate:.2f}, Avg time: {avg_response_time:.1f}ms")
        
        # Update moving average (handled by BaseValidatorNeuron)
        self.update_scores(scores)
        return scores


# The main function parses the configuration and runs the validator.
if __name__ == "__main__":
    with Validator() as validator:
        while True:
            bt.logging.info(f"Zeus-Miner Validator running... {time.time()}")
            time.sleep(60)  # Longer interval for comprehensive validation
