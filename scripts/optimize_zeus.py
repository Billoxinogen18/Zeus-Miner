#!/usr/bin/env python3
"""
Zeus-Miner Optimization Script

This script optimizes Zeus ASIC settings and mining parameters to maximize
performance and achieve top rankings on the Bittensor subnet.
"""

import argparse
import json
import time
import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.cgminer_api import CGMinerAPI
import bittensor as bt


class ZeusOptimizer:
    """Zeus mining optimization and performance tuning."""
    
    def __init__(self, cgminer_host="127.0.0.1", cgminer_port=4028):
        self.api = CGMinerAPI(host=cgminer_host, port=cgminer_port)
        self.optimization_history = []
        
        # Optimal Zeus ASIC frequencies (in MHz)
        self.zeus_frequencies = {
            'conservative': 250,  # Stable, low power
            'balanced': 300,      # Good balance
            'performance': 350,   # High performance
            'extreme': 382        # Maximum performance (higher risk)
        }
        
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for optimization process."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('zeus_optimization.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('ZeusOptimizer')
    
    def check_system_health(self):
        """Comprehensive system health check."""
        self.logger.info("Performing system health check...")
        
        health = self.api.health_check()
        
        if not health['cgminer_connected']:
            self.logger.error("cgminer is not running or not accessible")
            return False
            
        if health['devices_online'] == 0:
            self.logger.error("No Zeus devices are online")
            return False
            
        if health['avg_temperature'] > 85:
            self.logger.warning(f"High temperature detected: {health['avg_temperature']}°C")
            
        if not health['error_rate_acceptable']:
            self.logger.warning("High hardware error rate detected")
            
        self.logger.info(f"Health check complete - {health['devices_online']}/{health['total_devices']} devices online")
        return True
    
    def benchmark_current_performance(self, duration=300):
        """Benchmark current mining performance."""
        self.logger.info(f"Benchmarking performance for {duration} seconds...")
        
        start_stats = self.api.get_stats()
        start_time = time.time()
        
        time.sleep(duration)
        
        end_stats = self.api.get_stats()
        end_time = time.time()
        
        # Calculate performance metrics
        elapsed = end_time - start_time
        shares_gained = end_stats.accepted_shares - start_stats.accepted_shares
        hashrate_avg = (start_stats.hashrate + end_stats.hashrate) / 2
        
        performance = {
            'duration': elapsed,
            'hashrate_avg': hashrate_avg,
            'shares_per_minute': (shares_gained / elapsed) * 60 if elapsed > 0 else 0,
            'error_rate': (end_stats.hardware_errors - start_stats.hardware_errors) / shares_gained if shares_gained > 0 else 0,
            'timestamp': start_time
        }
        
        self.logger.info(f"Performance - Hashrate: {hashrate_avg:.0f} H/s, Shares/min: {performance['shares_per_minute']:.2f}")
        return performance
    
    def optimize_cgminer_settings(self):
        """Apply optimal cgminer settings for Zeus ASICs."""
        self.logger.info("Optimizing cgminer settings...")
        
        results = self.api.optimize_zeus_settings()
        
        success_count = 0
        for setting, result in results.items():
            if 'error' not in result:
                success_count += 1
                self.logger.info(f"Applied setting {setting}: OK")
            else:
                self.logger.warning(f"Failed to apply setting {setting}: {result['error']}")
        
        self.logger.info(f"Applied {success_count}/{len(results)} optimal settings")
        return success_count == len(results)
    
    def tune_zeus_frequency(self, mode='balanced'):
        """Tune Zeus ASIC frequency for optimal performance."""
        if mode not in self.zeus_frequencies:
            self.logger.error(f"Invalid frequency mode: {mode}")
            return False
            
        frequency = self.zeus_frequencies[mode]
        self.logger.info(f"Setting Zeus frequency to {frequency} MHz ({mode} mode)")
        
        devices = self.api.get_device_stats()
        success_count = 0
        
        for device in devices:
            try:
                result = self.api.set_zeus_frequency(device['id'], frequency)
                if 'error' not in str(result).lower():
                    success_count += 1
                    self.logger.info(f"Device {device['id']}: frequency set to {frequency} MHz")
                else:
                    self.logger.warning(f"Device {device['id']}: failed to set frequency")
            except Exception as e:
                self.logger.warning(f"Device {device['id']}: error setting frequency - {e}")
        
        self.logger.info(f"Successfully tuned {success_count}/{len(devices)} devices")
        return success_count > 0
    
    def monitor_stability(self, duration=600):
        """Monitor system stability after optimization."""
        self.logger.info(f"Monitoring stability for {duration} seconds...")
        
        start_time = time.time()
        stable = True
        
        while time.time() - start_time < duration:
            health = self.api.health_check()
            
            if not health['cgminer_connected']:
                self.logger.error("Lost connection to cgminer")
                stable = False
                break
                
            if health['avg_temperature'] > 90:
                self.logger.error(f"Critical temperature: {health['avg_temperature']}°C")
                stable = False
                break
                
            if not health['error_rate_acceptable']:
                self.logger.warning("High error rate detected during stability test")
                
            time.sleep(30)  # Check every 30 seconds
        
        self.logger.info(f"Stability test {'PASSED' if stable else 'FAILED'}")
        return stable
    
    def run_optimization_cycle(self, frequency_mode='balanced', benchmark_duration=300):
        """Run complete optimization cycle."""
        self.logger.info("Starting Zeus optimization cycle...")
        
        # 1. Health check
        if not self.check_system_health():
            self.logger.error("System health check failed - aborting optimization")
            return False
        
        # 2. Baseline benchmark
        self.logger.info("Taking baseline performance measurement...")
        baseline = self.benchmark_current_performance(benchmark_duration)
        
        # 3. Apply optimizations
        cgminer_ok = self.optimize_cgminer_settings()
        time.sleep(10)  # Let settings settle
        
        frequency_ok = self.tune_zeus_frequency(frequency_mode)
        time.sleep(30)  # Let frequency changes settle
        
        if not cgminer_ok and not frequency_ok:
            self.logger.error("All optimizations failed")
            return False
        
        # 4. Post-optimization benchmark
        self.logger.info("Measuring optimized performance...")
        optimized = self.benchmark_current_performance(benchmark_duration)
        
        # 5. Calculate improvement
        improvement = {
            'hashrate_change': optimized['hashrate_avg'] - baseline['hashrate_avg'],
            'hashrate_percent': ((optimized['hashrate_avg'] / baseline['hashrate_avg']) - 1) * 100 if baseline['hashrate_avg'] > 0 else 0,
            'shares_change': optimized['shares_per_minute'] - baseline['shares_per_minute'],
            'error_rate_change': optimized['error_rate'] - baseline['error_rate']
        }
        
        self.logger.info(f"Optimization results:")
        self.logger.info(f"  Hashrate: {improvement['hashrate_change']:+.0f} H/s ({improvement['hashrate_percent']:+.1f}%)")
        self.logger.info(f"  Shares/min: {improvement['shares_change']:+.2f}")
        self.logger.info(f"  Error rate: {improvement['error_rate_change']:+.4f}")
        
        # 6. Stability test if significant improvement
        if improvement['hashrate_percent'] > 5:
            self.logger.info("Significant improvement detected - running stability test...")
            stable = self.monitor_stability(600)
            if not stable:
                self.logger.warning("Optimization caused instability - consider reverting")
        
        # 7. Save optimization results
        result = {
            'timestamp': time.time(),
            'frequency_mode': frequency_mode,
            'baseline': baseline,
            'optimized': optimized,
            'improvement': improvement,
            'cgminer_optimized': cgminer_ok,
            'frequency_optimized': frequency_ok
        }
        
        self.optimization_history.append(result)
        self.save_optimization_history()
        
        return improvement['hashrate_percent'] > 0
    
    def save_optimization_history(self):
        """Save optimization history to file."""
        try:
            with open('zeus_optimization_history.json', 'w') as f:
                json.dump(self.optimization_history, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save optimization history: {e}")
    
    def load_optimization_history(self):
        """Load optimization history from file."""
        try:
            if os.path.exists('zeus_optimization_history.json'):
                with open('zeus_optimization_history.json', 'r') as f:
                    self.optimization_history = json.load(f)
                    self.logger.info(f"Loaded {len(self.optimization_history)} previous optimization records")
        except Exception as e:
            self.logger.warning(f"Failed to load optimization history: {e}")
    
    def generate_recommendations(self):
        """Generate optimization recommendations based on current performance."""
        self.logger.info("Analyzing system and generating recommendations...")
        
        health = self.api.health_check()
        performance = self.api.get_performance_metrics()
        recommendations = []
        
        # Temperature recommendations
        if health['avg_temperature'] > 80:
            recommendations.append("High temperature detected - improve cooling or reduce frequency")
        elif health['avg_temperature'] < 60:
            recommendations.append("Low temperature - can safely increase frequency for better performance")
        
        # Error rate recommendations
        if performance.get('error_rate', 0) > 0.02:
            recommendations.append("High error rate - reduce frequency or check device stability")
        
        # Hashrate recommendations
        expected_hashrate = health['devices_online'] * 50000  # Assume 50 KH/s per device
        actual_hashrate = performance.get('total_hashrate', 0)
        
        if actual_hashrate < expected_hashrate * 0.8:
            recommendations.append("Low hashrate detected - check device configuration and connections")
        
        # Efficiency recommendations
        efficiency = performance.get('efficiency', 0)
        if efficiency < 0.95:
            recommendations.append("Low mining efficiency - optimize cgminer settings")
        
        if not recommendations:
            recommendations.append("System is performing well - consider 'performance' frequency mode for higher hashrate")
        
        self.logger.info("Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            self.logger.info(f"  {i}. {rec}")
        
        return recommendations


def main():
    parser = argparse.ArgumentParser(description="Zeus-Miner Optimization Tool")
    parser.add_argument('--mode', choices=['conservative', 'balanced', 'performance', 'extreme'], 
                       default='balanced', help='Optimization mode')
    parser.add_argument('--benchmark-duration', type=int, default=300,
                       help='Benchmark duration in seconds')
    parser.add_argument('--host', default='127.0.0.1', help='cgminer API host')
    parser.add_argument('--port', type=int, default=4028, help='cgminer API port')
    parser.add_argument('--recommendations-only', action='store_true',
                       help='Only generate recommendations without applying changes')
    
    args = parser.parse_args()
    
    optimizer = ZeusOptimizer(cgminer_host=args.host, cgminer_port=args.port)
    optimizer.load_optimization_history()
    
    if args.recommendations_only:
        optimizer.generate_recommendations()
    else:
        success = optimizer.run_optimization_cycle(
            frequency_mode=args.mode,
            benchmark_duration=args.benchmark_duration
        )
        
        if success:
            print("\n✅ Optimization completed successfully!")
            print("Your Zeus miners should now achieve higher rankings on the subnet.")
        else:
            print("\n❌ Optimization failed or provided no improvement.")
            print("Check the logs for details and try a different optimization mode.")


if __name__ == "__main__":
    main()