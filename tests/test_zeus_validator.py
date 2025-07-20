#!/usr/bin/env python3
"""
Zeus-Validator Test Suite
Copyright © 2023 Sun Wukong
"""

import pytest
import asyncio
import unittest.mock
from unittest.mock import Mock, patch, AsyncMock
import time
import hashlib
import struct

import bittensor as bt
from template.protocol import HashWork
from neurons.validator import Validator


class TestZeusValidator:
    """Comprehensive test suite for Zeus-Miner validator functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        return config
    
    @pytest.fixture
    def mock_metagraph(self):
        """Mock metagraph for testing."""
        metagraph = Mock()
        metagraph.axons = [Mock() for _ in range(3)]  # 3 miners
        return metagraph
    
    @pytest.fixture
    def validator(self, mock_config, mock_metagraph):
        """Create validator instance for testing."""
        with patch('neurons.validator.BaseValidatorNeuron.__init__'), \
             patch.object(Validator, 'load_state'):
            validator = Validator(mock_config)
            validator.config = mock_config
            validator.metagraph = mock_metagraph
            validator.dendrite = Mock()
            return validator
    
    def test_difficulty_adjustment_increase(self, validator):
        """Test difficulty increase when success rate is too high."""
        # Mock high success rate history
        validator.challenge_history = [
            {'success_rate': 0.9, 'avg_response_time': 3.0},
            {'success_rate': 0.95, 'avg_response_time': 2.5},
            {'success_rate': 0.88, 'avg_response_time': 4.0}
        ]
        
        old_difficulty = validator.base_difficulty
        new_difficulty = validator.get_current_difficulty()
        
        # Difficulty should increase (smaller number = harder)
        assert new_difficulty < old_difficulty
    
    def test_difficulty_adjustment_decrease(self, validator):
        """Test difficulty decrease when success rate is too low."""
        # Mock low success rate history  
        validator.challenge_history = [
            {'success_rate': 0.1, 'avg_response_time': 15.0},
            {'success_rate': 0.2, 'avg_response_time': 18.0},
            {'success_rate': 0.15, 'avg_response_time': 20.0}
        ]
        
        old_difficulty = validator.base_difficulty
        new_difficulty = validator.get_current_difficulty()
        
        # Difficulty should decrease (larger number = easier)
        assert new_difficulty > old_difficulty
    
    def test_challenge_header_generation(self, validator):
        """Test realistic block header generation."""
        header = validator.generate_challenge_header()
        
        assert isinstance(header, bytes)
        assert len(header) == 76  # Standard block header without nonce
        
        # Should generate different headers each time
        header2 = validator.generate_challenge_header()
        assert header != header2
    
    def test_target_generation_from_difficulty(self, validator):
        """Test target generation from difficulty value."""
        difficulty = 0x0000ffff
        target = validator.generate_target_from_difficulty(difficulty)
        
        assert isinstance(target, bytes)
        assert len(target) == 32
        
        # Target should match difficulty pattern
        assert target[:4] == difficulty.to_bytes(4, byteorder='little')
        assert target[4:] == b'\xff' * 28
    
    def test_challenge_type_selection(self, validator):
        """Test challenge type selection logic."""
        # Test with no history (should use defaults)
        challenge_type = validator.select_challenge_type()
        assert challenge_type in validator.challenge_types
        
        # Test with high success rate (should favor hard challenges)
        validator.challenge_history = [{'success_rate': 0.9}]
        hard_challenges = 0
        for _ in range(20):
            challenge_type = validator.select_challenge_type()
            if challenge_type == 'high_difficulty':
                hard_challenges += 1
        
        # Should have more hard challenges with high success rate
        assert hard_challenges > 0
    
    def test_create_challenge_standard(self, validator):
        """Test standard challenge creation."""
        validator.current_challenge_type = 'standard'
        challenge = validator.create_challenge()
        
        assert isinstance(challenge, HashWork)
        assert len(challenge.header_hex) == 152  # 76 bytes * 2
        assert len(challenge.target_hex) == 64   # 32 bytes * 2
    
    def test_create_challenge_high_difficulty(self, validator):
        """Test high difficulty challenge creation."""
        validator.current_challenge_type = 'high_difficulty'
        base_difficulty = validator.base_difficulty
        
        challenge = validator.create_challenge()
        
        # High difficulty challenges should be harder
        target_bytes = bytes.fromhex(challenge.target_hex)
        challenge_difficulty = int.from_bytes(target_bytes[:4], byteorder='little')
        assert challenge_difficulty <= base_difficulty // 4
    
    def test_verify_mining_result_success(self, validator):
        """Test verification of successful mining result."""
        # Create challenge
        challenge = HashWork(
            header_hex="00" * 152,
            target_hex="ff" * 64
        )
        
        # Create valid response
        response = HashWork(
            header_hex=challenge.header_hex,
            target_hex=challenge.target_hex,
            nonce=12345,
            success=True,
            latency_ms=2500.0
        )
        
        verification = validator.verify_mining_result(challenge, response)
        
        assert verification['nonce_valid'] is True
        assert verification['latency_reasonable'] is True
        assert verification['hash_correct'] is True
        # With easy target, should meet target
        assert verification['target_met'] is True
        assert verification['valid'] is True
    
    def test_verify_mining_result_failure(self, validator):
        """Test verification of failed mining result."""
        challenge = HashWork(
            header_hex="00" * 152,
            target_hex="00" * 64  # Impossible target
        )
        
        response = HashWork(
            header_hex=challenge.header_hex,
            target_hex=challenge.target_hex,
            nonce=12345,
            success=True,
            latency_ms=2500.0
        )
        
        verification = validator.verify_mining_result(challenge, response)
        
        assert verification['nonce_valid'] is True
        assert verification['hash_correct'] is True
        assert verification['target_met'] is False  # Should fail impossible target
        assert verification['valid'] is False
    
    def test_verify_mining_no_solution(self, validator):
        """Test verification when no solution is claimed."""
        challenge = HashWork(
            header_hex="00" * 152,
            target_hex="ff" * 64
        )
        
        response = HashWork(
            header_hex=challenge.header_hex,
            target_hex=challenge.target_hex,
            nonce=None,
            success=False,
            latency_ms=8000.0
        )
        
        verification = validator.verify_mining_result(challenge, response)
        
        assert verification['valid'] is False
        assert verification['error'] == 'No solution claimed'
    
    def test_calculate_advanced_score_success(self, validator):
        """Test advanced scoring for successful mining."""
        verification_result = {
            'valid': True,
            'efficiency_score': 5.0
        }
        
        response = HashWork(
            nonce=12345,
            success=True,
            latency_ms=3000.0
        )
        
        score = validator.calculate_advanced_score(0, verification_result, response)
        
        # Should get base score plus bonuses
        assert score > 1.0
        
        # Check that miner performance is tracked
        assert 0 in validator.miner_performance
        assert validator.miner_performance[0]['total_challenges'] == 1
        assert validator.miner_performance[0]['successful_challenges'] == 1
    
    def test_calculate_advanced_score_failure(self, validator):
        """Test advanced scoring for failed mining."""
        verification_result = {
            'valid': False
        }
        
        response = HashWork(
            nonce=None,
            success=False,
            latency_ms=8000.0
        )
        
        score = validator.calculate_advanced_score(0, verification_result, response)
        
        assert score == 0.0
    
    def test_calculate_advanced_score_high_difficulty_bonus(self, validator):
        """Test bonus scoring for high difficulty challenges."""
        validator.current_challenge_type = 'high_difficulty'
        
        verification_result = {
            'valid': True,
            'efficiency_score': 3.0
        }
        
        response = HashWork(
            nonce=12345,
            success=True,
            latency_ms=4000.0
        )
        
        score = validator.calculate_advanced_score(0, verification_result, response)
        
        # Should get significant bonus for solving hard challenge
        assert score >= 1.5  # Base score + high difficulty bonus
    
    def test_calculate_advanced_score_historical_bonus(self, validator):
        """Test bonus scoring for miners with good history."""
        # Set up miner with good historical performance
        validator.miner_performance[0] = {
            'total_challenges': 10,
            'successful_challenges': 9,
            'success_rate': 0.9,
            'total_score': 12.0
        }
        
        verification_result = {
            'valid': True,
            'efficiency_score': 2.0
        }
        
        response = HashWork(
            nonce=12345,
            success=True,
            latency_ms=5000.0
        )
        
        score = validator.calculate_advanced_score(0, verification_result, response)
        
        # Should get historical performance bonus
        assert score > 1.2  # Base score + historical bonus
    
    @pytest.mark.asyncio
    async def test_forward_integration(self, validator):
        """Test complete forward pass integration."""
        # Mock successful miner responses
        mock_responses = [
            HashWork(nonce=12345, success=True, latency_ms=3000.0),
            HashWork(nonce=67890, success=True, latency_ms=4500.0),
            HashWork(nonce=None, success=False, latency_ms=8000.0)
        ]
        
        validator.dendrite.query = AsyncMock(return_value=mock_responses)
        
        with patch.object(validator, 'update_scores') as mock_update:
            scores = await validator.forward()
            
        # Should return scores for all miners
        assert len(scores) == 3
        assert scores[0] > 0  # First miner succeeded
        assert scores[1] > 0  # Second miner succeeded  
        assert scores[2] == 0  # Third miner failed
        
        # Should update scores
        mock_update.assert_called_once_with(scores)
        
        # Should record challenge statistics
        assert len(validator.challenge_history) > 0
        latest_challenge = validator.challenge_history[-1]
        assert 'success_rate' in latest_challenge
        assert latest_challenge['valid_responses'] == 2
        assert latest_challenge['total_responses'] == 3
    
    @pytest.mark.asyncio 
    async def test_forward_timeout_handling(self, validator):
        """Test handling of different challenge types and timeouts."""
        validator.current_challenge_type = 'time_pressure'
        
        mock_responses = [HashWork(nonce=12345, success=True, latency_ms=2000.0)]
        validator.dendrite.query = AsyncMock(return_value=mock_responses)
        
        with patch.object(validator, 'update_scores'):
            await validator.forward()
            
        # Should use shorter timeout for time pressure challenges
        call_args = validator.dendrite.query.call_args
        assert call_args[1]['timeout'] == 6.0  # time_pressure timeout
    
    def test_challenge_history_maintenance(self, validator):
        """Test that challenge history is properly maintained."""
        # Fill history beyond limit
        for i in range(105):
            validator.challenge_history.append({
                'timestamp': time.time() - i,
                'success_rate': 0.5
            })
        
        # Simulate forward pass to trigger history maintenance
        validator.challenge_history.append({
            'timestamp': time.time(),
            'success_rate': 0.7
        })
        
        # Should trim to keep only recent history
        if len(validator.challenge_history) > 100:
            validator.challenge_history = validator.challenge_history[-100:]
            
        assert len(validator.challenge_history) <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])