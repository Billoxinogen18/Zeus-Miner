import json
import socket
import time
import typing
import threading
import logging
from dataclasses import dataclass


@dataclass
class MiningStats:
    """Mining statistics from cgminer."""
    hashrate: float = 0.0
    accepted_shares: int = 0
    rejected_shares: int = 0
    hardware_errors: int = 0
    temperature: float = 0.0
    fan_speed: int = 0
    uptime: int = 0
    difficulty: float = 0.0


class CGMinerAPI:
    """Enhanced wrapper around cgminer JSON API with Zeus ASIC optimizations."""

    def __init__(self, host: str = "127.0.0.1", port: int = 4028, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.connection_retries = 3
        self.retry_delay = 1.0
        
    def _query_with_retry(self, payload: dict) -> typing.Any:
        """Query cgminer with automatic retry on failure."""
        last_exception = None
        
        for attempt in range(self.connection_retries):
            try:
                return self._query(payload)
            except Exception as e:
                last_exception = e
                if attempt < self.connection_retries - 1:
                    time.sleep(self.retry_delay)
                    
        raise last_exception or ConnectionError("Failed to connect to cgminer")

    def _query(self, payload: dict) -> typing.Any:
        """Send JSON query to cgminer API."""
        line = json.dumps(payload) + "\n"
        
        try:
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                sock.sendall(line.encode())
                sock.shutdown(socket.SHUT_WR)
                
                # Read response with buffer handling
                data = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    
        except socket.timeout:
            raise TimeoutError(f"cgminer API timeout after {self.timeout}s")
        except socket.error as e:
            raise ConnectionError(f"cgminer connection failed: {e}")
            
        if not data:
            raise ValueError("Empty response from cgminer")
            
        # Handle multiple JSON objects concatenated
        if b"}{" in data:
            data = b"[" + data.replace(b"}{", b"},{") + b"]"
            return json.loads(data.decode())
        
        try:
            return json.loads(data.decode())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")

    def is_connected(self) -> bool:
        """Check if cgminer is accessible."""
        try:
            self.version()
            return True
        except:
            return False

    def version(self) -> dict:
        """Get cgminer version information."""
        return self._query_with_retry({"command": "version"})

    def summary(self) -> dict:
        """Get mining summary statistics."""
        return self._query_with_retry({"command": "summary"})

    def get_stats(self) -> MiningStats:
        """Get parsed mining statistics."""
        try:
            summary_data = self.summary()
            summary = summary_data.get("SUMMARY", [{}])[0]
            
            return MiningStats(
                hashrate=float(summary.get("KHS 5s", 0)) * 1000,  # Convert to H/s
                accepted_shares=int(summary.get("Accepted", 0)),
                rejected_shares=int(summary.get("Rejected", 0)),
                hardware_errors=int(summary.get("Hardware Errors", 0)),
                uptime=int(summary.get("Elapsed", 0)),
                difficulty=float(summary.get("Difficulty Accepted", 0))
            )
        except Exception as e:
            logging.warning(f"Failed to parse mining stats: {e}")
            return MiningStats()

    def devs(self) -> dict:
        """Get device information for Zeus ASICs."""
        return self._query_with_retry({"command": "devs"})

    def get_device_stats(self) -> typing.List[dict]:
        """Get detailed Zeus ASIC device statistics."""
        try:
            devs_data = self.devs()
            devices = devs_data.get("DEVS", [])
            
            zeus_devices = []
            for dev in devices:
                if "zeus" in dev.get("Name", "").lower():
                    zeus_devices.append({
                        "id": dev.get("ID", -1),
                        "name": dev.get("Name", "Unknown"),
                        "enabled": dev.get("Enabled", "N") == "Y",
                        "status": dev.get("Status", "Unknown"),
                        "temperature": float(dev.get("Temperature", 0)),
                        "hashrate": float(dev.get("KHS 5s", 0)) * 1000,
                        "accepted": int(dev.get("Accepted", 0)),
                        "rejected": int(dev.get("Rejected", 0)),
                        "hardware_errors": int(dev.get("Hardware Errors", 0))
                    })
            
            return zeus_devices
            
        except Exception as e:
            logging.warning(f"Failed to get device stats: {e}")
            return []

    def pools(self) -> dict:
        """Get pool information."""
        return self._query_with_retry({"command": "pools"})

    def get_work(self) -> dict:
        """Request work from cgminer (requires pool connection)."""
        return self._query_with_retry({"command": "getwork"})

    def submit_work(self, work_data: str) -> dict:
        """Submit completed work to cgminer."""
        return self._query_with_retry({
            "command": "submitwork",
            "parameter": work_data
        })

    def notify(self) -> dict:
        """Get notification/status updates."""
        return self._query_with_retry({"command": "notify"})

    def restart(self) -> dict:
        """Restart cgminer."""
        return self._query_with_retry({"command": "restart"})

    def quit(self) -> dict:
        """Quit cgminer."""
        return self._query_with_retry({"command": "quit"})

    def enable_device(self, device_id: int) -> dict:
        """Enable a specific Zeus ASIC device."""
        return self._query_with_retry({
            "command": "gpuenable",
            "parameter": str(device_id)
        })

    def disable_device(self, device_id: int) -> dict:
        """Disable a specific Zeus ASIC device."""
        return self._query_with_retry({
            "command": "gpudisable", 
            "parameter": str(device_id)
        })

    def set_zeus_frequency(self, device_id: int, frequency: int) -> dict:
        """Set Zeus ASIC frequency (experimental)."""
        # Note: This may require custom cgminer_zeus commands
        return self._query_with_retry({
            "command": "zeusset",
            "parameter": f"{device_id},{frequency}"
        })

    def optimize_zeus_settings(self) -> dict:
        """Apply optimal settings for Zeus ASICs."""
        # Recommended Zeus mining settings
        optimizations = {
            "queue": 2,           # Optimal queue depth
            "scan_time": 15,      # Scan time for work requests
            "expiry": 120,        # Work expiry time
            "log_interval": 5     # Log interval
        }
        
        results = {}
        for setting, value in optimizations.items():
            try:
                result = self._query_with_retry({
                    "command": "set",
                    "parameter": f"{setting},{value}"
                })
                results[setting] = result
            except Exception as e:
                results[setting] = {"error": str(e)}
                
        return results

    def get_performance_metrics(self) -> dict:
        """Get comprehensive performance metrics for ranking optimization."""
        try:
            stats = self.get_stats()
            devices = self.get_device_stats()
            
            # Calculate efficiency metrics
            total_hashrate = sum(dev["hashrate"] for dev in devices)
            total_shares = stats.accepted_shares + stats.rejected_shares
            efficiency = stats.accepted_shares / total_shares if total_shares > 0 else 0
            
            return {
                "total_hashrate": total_hashrate,
                "device_count": len(devices),
                "efficiency": efficiency,
                "uptime": stats.uptime,
                "avg_temperature": sum(dev["temperature"] for dev in devices) / len(devices) if devices else 0,
                "error_rate": stats.hardware_errors / total_shares if total_shares > 0 else 0,
                "shares_per_minute": stats.accepted_shares / (stats.uptime / 60) if stats.uptime > 0 else 0
            }
            
        except Exception as e:
            logging.error(f"Failed to get performance metrics: {e}")
            return {}

    def health_check(self) -> dict:
        """Comprehensive health check for Zeus mining setup."""
        health_status = {
            "cgminer_connected": False,
            "devices_online": 0,
            "total_devices": 0,
            "avg_temperature": 0.0,
            "hashrate_stable": False,
            "error_rate_acceptable": True,
            "recommendations": []
        }
        
        try:
            # Check cgminer connection
            health_status["cgminer_connected"] = self.is_connected()
            
            if health_status["cgminer_connected"]:
                devices = self.get_device_stats()
                health_status["total_devices"] = len(devices)
                health_status["devices_online"] = len([d for d in devices if d["enabled"]])
                
                if devices:
                    temps = [d["temperature"] for d in devices if d["temperature"] > 0]
                    health_status["avg_temperature"] = sum(temps) / len(temps) if temps else 0
                    
                    # Check for overheating
                    if health_status["avg_temperature"] > 80:
                        health_status["recommendations"].append("High temperature detected - check cooling")
                    
                    # Check error rates
                    total_accepted = sum(d["accepted"] for d in devices)
                    total_errors = sum(d["hardware_errors"] for d in devices)
                    if total_accepted > 0 and (total_errors / total_accepted) > 0.02:
                        health_status["error_rate_acceptable"] = False
                        health_status["recommendations"].append("High hardware error rate - check device stability")
                
                # Check hashrate stability
                stats = self.get_stats()
                if stats.hashrate > 0:
                    health_status["hashrate_stable"] = True
                else:
                    health_status["recommendations"].append("No hashrate detected - check device connectivity")
                    
        except Exception as e:
            health_status["recommendations"].append(f"Health check failed: {e}")
            
        return health_status 