#!/usr/bin/env python3
"""
Zeus-Miner Performance Monitor

Real-time monitoring of mining performance, subnet rankings, and system health
to ensure optimal performance and top rankings.
"""

import argparse
import time
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import threading
from typing import Dict, List
import signal

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.cgminer_api import CGMinerAPI
import bittensor as bt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text


class PerformanceMonitor:
    """Real-time performance monitoring for Zeus-Miner."""
    
    def __init__(self, cgminer_host="127.0.0.1", cgminer_port=4028, update_interval=30):
        self.api = CGMinerAPI(host=cgminer_host, port=cgminer_port)
        self.update_interval = update_interval
        self.console = Console()
        
        # Performance history
        self.performance_history = []
        self.ranking_history = []
        
        # Monitoring flags
        self.monitoring = False
        self.monitoring_thread = None
        
        # Alert thresholds
        self.alert_thresholds = {
            'temperature': 85.0,
            'error_rate': 0.02,
            'hashrate_drop': 0.15,  # 15% drop threshold
            'ranking_drop': 5       # positions
        }
        
        # Current state
        self.current_metrics = {}
        self.subnet_info = {}
        self.alerts = []
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.console.print("\n[yellow]Shutting down monitor...[/yellow]")
        self.stop_monitoring()
        sys.exit(0)
    
    def get_current_metrics(self) -> Dict:
        """Get current mining and system metrics."""
        try:
            # Mining performance
            stats = self.api.get_stats()
            devices = self.api.get_device_stats()
            health = self.api.health_check()
            
            # Calculate derived metrics
            total_hashrate = sum(dev['hashrate'] for dev in devices)
            avg_temperature = sum(dev['temperature'] for dev in devices) / len(devices) if devices else 0
            
            metrics = {
                'timestamp': time.time(),
                'hashrate': total_hashrate,
                'accepted_shares': stats.accepted_shares,
                'rejected_shares': stats.rejected_shares,
                'hardware_errors': stats.hardware_errors,
                'uptime': stats.uptime,
                'devices_online': len([d for d in devices if d['enabled']]),
                'total_devices': len(devices),
                'avg_temperature': avg_temperature,
                'error_rate': stats.hardware_errors / (stats.accepted_shares + stats.rejected_shares) if (stats.accepted_shares + stats.rejected_shares) > 0 else 0,
                'efficiency': stats.accepted_shares / (stats.accepted_shares + stats.rejected_shares) if (stats.accepted_shares + stats.rejected_shares) > 0 else 0,
                'cgminer_connected': health['cgminer_connected']
            }
            
            return metrics
            
        except Exception as e:
            self.console.print(f"[red]Error getting metrics: {e}[/red]")
            return {}
    
    def get_subnet_ranking(self) -> Dict:
        """Get current subnet ranking information."""
        try:
            # This would typically query the subtensor for ranking info
            # For now, return mock data structure
            ranking_info = {
                'current_rank': 8,  # Mock ranking
                'total_miners': 50,
                'percentile': 0.16,  # Top 16%
                'emission_rate': 0.025,  # TAO per hour
                'stake_amount': 1500.0,
                'incentive': 0.94,
                'trust': 0.88,
                'consensus': 0.91
            }
            
            return ranking_info
            
        except Exception as e:
            self.console.print(f"[red]Error getting subnet ranking: {e}[/red]")
            return {}
    
    def check_alerts(self, metrics: Dict, ranking: Dict):
        """Check for alert conditions."""
        new_alerts = []
        
        # Temperature alerts
        if metrics.get('avg_temperature', 0) > self.alert_thresholds['temperature']:
            new_alerts.append({
                'type': 'CRITICAL',
                'message': f"High temperature: {metrics['avg_temperature']:.1f}°C",
                'timestamp': time.time()
            })
        
        # Error rate alerts
        if metrics.get('error_rate', 0) > self.alert_thresholds['error_rate']:
            new_alerts.append({
                'type': 'WARNING',
                'message': f"High error rate: {metrics['error_rate']:.2%}",
                'timestamp': time.time()
            })
        
        # Hashrate drop alerts
        if len(self.performance_history) > 5:
            recent_avg = sum(h['hashrate'] for h in self.performance_history[-5:]) / 5
            current_hashrate = metrics.get('hashrate', 0)
            if current_hashrate < recent_avg * (1 - self.alert_thresholds['hashrate_drop']):
                new_alerts.append({
                    'type': 'WARNING',
                    'message': f"Hashrate drop: {current_hashrate:.0f} H/s (was {recent_avg:.0f} H/s)",
                    'timestamp': time.time()
                })
        
        # Ranking alerts
        if len(self.ranking_history) > 2:
            prev_rank = self.ranking_history[-2].get('current_rank', 999)
            current_rank = ranking.get('current_rank', 999)
            if current_rank > prev_rank + self.alert_thresholds['ranking_drop']:
                new_alerts.append({
                    'type': 'WARNING',
                    'message': f"Ranking dropped: #{current_rank} (was #{prev_rank})",
                    'timestamp': time.time()
                })
        
        # Device offline alerts
        if metrics.get('devices_online', 0) < metrics.get('total_devices', 0):
            offline = metrics['total_devices'] - metrics['devices_online']
            new_alerts.append({
                'type': 'WARNING',
                'message': f"{offline} device(s) offline",
                'timestamp': time.time()
            })
        
        # Connection alerts
        if not metrics.get('cgminer_connected', False):
            new_alerts.append({
                'type': 'CRITICAL',
                'message': "Lost connection to cgminer",
                'timestamp': time.time()
            })
        
        # Add new alerts and keep only recent ones
        self.alerts.extend(new_alerts)
        self.alerts = self.alerts[-20:]  # Keep last 20 alerts
        
        return new_alerts
    
    def create_dashboard(self) -> Layout:
        """Create the monitoring dashboard layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=8)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="metrics"),
            Layout(name="devices")
        )
        
        layout["right"].split_column(
            Layout(name="ranking"),
            Layout(name="performance")
        )
        
        # Header
        header_text = Text("Zeus-Miner Performance Monitor", style="bold blue")
        header_text.append(f" - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
        layout["header"].update(Panel(header_text, border_style="blue"))
        
        # Metrics panel
        metrics_table = Table(title="Current Metrics", show_header=True, header_style="bold magenta")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        metrics_table.add_column("Status", style="yellow")
        
        if self.current_metrics:
            m = self.current_metrics
            metrics_table.add_row("Hashrate", f"{m.get('hashrate', 0):,.0f} H/s", "✓" if m.get('hashrate', 0) > 0 else "✗")
            metrics_table.add_row("Devices", f"{m.get('devices_online', 0)}/{m.get('total_devices', 0)}", "✓" if m.get('devices_online', 0) == m.get('total_devices', 0) else "⚠")
            metrics_table.add_row("Temperature", f"{m.get('avg_temperature', 0):.1f}°C", "✓" if m.get('avg_temperature', 0) < 80 else "⚠")
            metrics_table.add_row("Error Rate", f"{m.get('error_rate', 0):.2%}", "✓" if m.get('error_rate', 0) < 0.02 else "⚠")
            metrics_table.add_row("Efficiency", f"{m.get('efficiency', 0):.1%}", "✓" if m.get('efficiency', 0) > 0.95 else "⚠")
            metrics_table.add_row("Uptime", f"{m.get('uptime', 0) // 3600:.0f}h {(m.get('uptime', 0) % 3600) // 60:.0f}m", "✓")
        
        layout["metrics"].update(Panel(metrics_table, border_style="green"))
        
        # Device status
        device_table = Table(title="Device Status", show_header=True, header_style="bold magenta")
        device_table.add_column("Device", style="cyan")
        device_table.add_column("Status", style="green")
        device_table.add_column("Hashrate", style="yellow")
        device_table.add_column("Temp", style="red")
        
        try:
            devices = self.api.get_device_stats()
            for dev in devices[:5]:  # Show first 5 devices
                status = "✓" if dev['enabled'] else "✗"
                device_table.add_row(
                    f"#{dev['id']}",
                    status,
                    f"{dev['hashrate']:,.0f} H/s",
                    f"{dev['temperature']:.0f}°C"
                )
        except:
            device_table.add_row("N/A", "Connection Error", "0", "0")
        
        layout["devices"].update(Panel(device_table, border_style="yellow"))
        
        # Ranking panel
        ranking_table = Table(title="Subnet Ranking", show_header=True, header_style="bold magenta")
        ranking_table.add_column("Metric", style="cyan")
        ranking_table.add_column("Value", style="green")
        ranking_table.add_column("Target", style="blue")
        
        if self.subnet_info:
            s = self.subnet_info
            ranking_table.add_row("Current Rank", f"#{s.get('current_rank', '?')}", "Top 10")
            ranking_table.add_row("Percentile", f"{s.get('percentile', 0):.1%}", "< 20%")
            ranking_table.add_row("Emission Rate", f"{s.get('emission_rate', 0):.3f} TAO/h", "> 0.02")
            ranking_table.add_row("Incentive", f"{s.get('incentive', 0):.2f}", "> 0.9")
            ranking_table.add_row("Trust", f"{s.get('trust', 0):.2f}", "> 0.8")
            ranking_table.add_row("Consensus", f"{s.get('consensus', 0):.2f}", "> 0.8")
        
        layout["ranking"].update(Panel(ranking_table, border_style="blue"))
        
        # Performance trend
        perf_text = "Performance Trend (Last 10 Updates):\n\n"
        if len(self.performance_history) >= 2:
            recent = self.performance_history[-10:]
            for i, h in enumerate(recent):
                timestamp = datetime.fromtimestamp(h['timestamp']).strftime('%H:%M:%S')
                hashrate = h['hashrate']
                trend = ""
                if i > 0:
                    prev_hashrate = recent[i-1]['hashrate']
                    if hashrate > prev_hashrate * 1.05:
                        trend = " ↗"
                    elif hashrate < prev_hashrate * 0.95:
                        trend = " ↘"
                    else:
                        trend = " →"
                perf_text += f"{timestamp}: {hashrate:,.0f} H/s{trend}\n"
        else:
            perf_text += "Collecting data..."
        
        layout["performance"].update(Panel(perf_text, title="Performance History", border_style="cyan"))
        
        # Footer - Alerts
        alert_text = "Recent Alerts:\n\n"
        if self.alerts:
            for alert in self.alerts[-5:]:  # Last 5 alerts
                alert_time = datetime.fromtimestamp(alert['timestamp']).strftime('%H:%M:%S')
                alert_type = alert['type']
                color = "red" if alert_type == "CRITICAL" else "yellow"
                alert_text += f"[{color}]{alert_time} [{alert_type}] {alert['message']}[/{color}]\n"
        else:
            alert_text += "[green]No alerts - system running normally[/green]"
        
        layout["footer"].update(Panel(alert_text, title="System Alerts", border_style="red"))
        
        return layout
    
    def monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                # Get current metrics
                metrics = self.get_current_metrics()
                ranking = self.get_subnet_ranking()
                
                if metrics:
                    self.current_metrics = metrics
                    self.performance_history.append(metrics)
                    
                    # Keep only recent history
                    if len(self.performance_history) > 100:
                        self.performance_history = self.performance_history[-100:]
                
                if ranking:
                    self.subnet_info = ranking
                    self.ranking_history.append(ranking)
                    
                    if len(self.ranking_history) > 50:
                        self.ranking_history = self.ranking_history[-50:]
                
                # Check for alerts
                if metrics and ranking:
                    new_alerts = self.check_alerts(metrics, ranking)
                    
                    # Print urgent alerts to console
                    for alert in new_alerts:
                        if alert['type'] == 'CRITICAL':
                            self.console.print(f"[bold red]CRITICAL ALERT: {alert['message']}[/bold red]")
                
                # Save performance data
                self.save_performance_data()
                
            except Exception as e:
                self.console.print(f"[red]Monitoring error: {e}[/red]")
            
            time.sleep(self.update_interval)
    
    def save_performance_data(self):
        """Save performance data to file."""
        try:
            data = {
                'performance_history': self.performance_history[-50:],  # Keep recent data
                'ranking_history': self.ranking_history[-20:],
                'alerts': self.alerts[-10:]
            }
            
            with open('zeus_performance_data.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            pass  # Silent fail for data saving
    
    def load_performance_data(self):
        """Load previous performance data."""
        try:
            if os.path.exists('zeus_performance_data.json'):
                with open('zeus_performance_data.json', 'r') as f:
                    data = json.load(f)
                    self.performance_history = data.get('performance_history', [])
                    self.ranking_history = data.get('ranking_history', [])
                    self.alerts = data.get('alerts', [])
        except Exception as e:
            pass  # Silent fail for data loading
    
    def start_monitoring(self):
        """Start the monitoring process."""
        self.load_performance_data()
        self.monitoring = True
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Start live dashboard
        with Live(self.create_dashboard(), refresh_per_second=1, screen=True) as live:
            while self.monitoring:
                live.update(self.create_dashboard())
                time.sleep(1)
    
    def stop_monitoring(self):
        """Stop the monitoring process."""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description="Zeus-Miner Performance Monitor")
    parser.add_argument('--host', default='127.0.0.1', help='cgminer API host')
    parser.add_argument('--port', type=int, default=4028, help='cgminer API port')
    parser.add_argument('--interval', type=int, default=30, help='Update interval in seconds')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(
        cgminer_host=args.host,
        cgminer_port=args.port,
        update_interval=args.interval
    )
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    main()