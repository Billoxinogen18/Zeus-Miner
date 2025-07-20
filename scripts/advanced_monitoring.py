#!/usr/bin/env python3
"""
Zeus-Miner Advanced Performance Monitoring Dashboard

Real-time monitoring system with ranking analytics, performance optimization,
and competitive intelligence for achieving top 5 Bittensor rankings.
"""

import time
import json
import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.text import Text
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available - using basic console output")
    # Mock classes for when Rich is not available
    class Layout:
        pass
    class Panel:
        pass
    class Table:
        pass
    class Text:
        pass

from utils.cgminer_api import CGMinerAPI


class AdvancedMonitor:
    """Advanced monitoring system for Zeus-Miner optimization."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.api = CGMinerAPI()
        self.performance_history = []
        self.ranking_data = []
        self.optimization_targets = {
            'ranking_position': 5,
            'success_rate': 0.95,
            'avg_response_time': 3000,
            'uptime': 0.995,
            'efficiency': 0.98
        }
        self.start_time = time.time()
        
    def get_current_metrics(self) -> Dict:
        """Get current comprehensive performance metrics."""
        try:
            # Mock current metrics - in production these would come from actual APIs
            current_metrics = {
                'timestamp': time.time(),
                'ranking': {
                    'current_position': 8,
                    'target_position': 5,
                    'percentile': 0.16,
                    'trend': 'improving',
                    'score': 0.847,
                    'gap_to_top5': 0.123
                },
                'performance': {
                    'success_rate': 0.91,
                    'avg_response_time': 3200,  # ms
                    'hashrate': 48500.0,  # KH/s
                    'uptime': 0.992,
                    'efficiency': 0.94,
                    'error_rate': 0.009
                },
                'hardware': {
                    'temperature': 72.5,
                    'frequency': 340,  # MHz
                    'power_usage': 45.2,  # W
                    'fan_speed': 2400,  # RPM
                    'health_status': 'optimal'
                },
                'network': {
                    'latency': 45.2,  # ms
                    'packet_loss': 0.001,
                    'connection_quality': 'excellent',
                    'validator_connections': 12
                },
                'economics': {
                    'tao_earned_today': 0.0347,
                    'projected_daily': 0.0412,
                    'efficiency_bonus': 0.0065,
                    'ranking_bonus': 0.0089
                }
            }
            
            # Add to history
            self.performance_history.append(current_metrics)
            
            # Keep only last 1000 entries
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
                
            return current_metrics
            
        except Exception as e:
            return {'error': str(e), 'timestamp': time.time()}
    
    def calculate_trend_analysis(self) -> Dict:
        """Calculate performance trends over time."""
        if len(self.performance_history) < 2:
            return {'insufficient_data': True}
        
        recent = self.performance_history[-10:]  # Last 10 measurements
        older = self.performance_history[-20:-10] if len(self.performance_history) >= 20 else []
        
        if not older:
            return {'insufficient_data': True}
        
        # Calculate trends
        trends = {}
        metrics_to_track = ['success_rate', 'avg_response_time', 'hashrate', 'efficiency']
        
        for metric in metrics_to_track:
            recent_avg = statistics.mean([m['performance'][metric] for m in recent if 'performance' in m])
            older_avg = statistics.mean([m['performance'][metric] for m in older if 'performance' in m])
            
            change = ((recent_avg - older_avg) / older_avg) * 100 if older_avg != 0 else 0
            
            trends[metric] = {
                'recent_avg': recent_avg,
                'older_avg': older_avg,
                'change_percent': change,
                'direction': 'improving' if change > 0 else 'declining' if change < 0 else 'stable'
            }
        
        return trends
    
    def generate_optimization_recommendations(self, metrics: Dict) -> List[Dict]:
        """Generate specific optimization recommendations based on current metrics."""
        recommendations = []
        
        perf = metrics.get('performance', {})
        hardware = metrics.get('hardware', {})
        ranking = metrics.get('ranking', {})
        
        # Success rate optimization
        if perf.get('success_rate', 0) < self.optimization_targets['success_rate']:
            gap = self.optimization_targets['success_rate'] - perf.get('success_rate', 0)
            recommendations.append({
                'category': 'performance',
                'priority': 'high' if gap > 0.05 else 'medium',
                'title': 'Improve Success Rate',
                'description': f"Success rate {perf.get('success_rate', 0):.1%} below target {self.optimization_targets['success_rate']:.1%}",
                'actions': [
                    'Optimize Zeus ASIC frequency',
                    'Improve thermal management',
                    'Fine-tune cgminer settings'
                ]
            })
        
        # Response time optimization  
        if perf.get('avg_response_time', 0) > self.optimization_targets['avg_response_time']:
            recommendations.append({
                'category': 'speed',
                'priority': 'high',
                'title': 'Reduce Response Time',
                'description': f"Response time {perf.get('avg_response_time', 0)}ms above target {self.optimization_targets['avg_response_time']}ms",
                'actions': [
                    'Increase Zeus frequency if temperature allows',
                    'Reduce cgminer scan time',
                    'Optimize network latency'
                ]
            })
        
        # Temperature management
        if hardware.get('temperature', 0) > 75:
            recommendations.append({
                'category': 'thermal',
                'priority': 'critical' if hardware.get('temperature', 0) > 85 else 'high',
                'title': 'Temperature Management',
                'description': f"Temperature {hardware.get('temperature', 0):.1f}°C requires attention",
                'actions': [
                    'Increase fan speed',
                    'Check thermal paste application',
                    'Improve case ventilation',
                    'Consider underclocking if critical'
                ]
            })
        
        # Ranking improvement
        if ranking.get('current_position', 10) > self.optimization_targets['ranking_position']:
            recommendations.append({
                'category': 'ranking',
                'priority': 'critical',
                'title': 'Ranking Improvement',
                'description': f"Current rank #{ranking.get('current_position', 0)} needs improvement to reach top 5",
                'actions': [
                    'Implement consensus tracking optimization',
                    'Enable early miner detection',
                    'Optimize for validator stake weighting',
                    'Improve mining efficiency'
                ]
            })
        
        return recommendations
    
    def create_dashboard_layout(self, metrics: Dict) -> Layout:
        """Create rich dashboard layout."""
        if not RICH_AVAILABLE:
            return None
            
        layout = Layout()
        
        # Split into main sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Split main section
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Split left section
        layout["left"].split_column(
            Layout(name="ranking", size=8),
            Layout(name="performance", size=10),
            Layout(name="hardware", size=8)
        )
        
        # Split right section
        layout["right"].split_column(
            Layout(name="trends", size=10),
            Layout(name="recommendations", size=16)
        )
        
        # Add content to each section
        layout["header"].update(self.create_header_panel())
        layout["ranking"].update(self.create_ranking_panel(metrics))
        layout["performance"].update(self.create_performance_panel(metrics))
        layout["hardware"].update(self.create_hardware_panel(metrics))
        layout["trends"].update(self.create_trends_panel(metrics))
        layout["recommendations"].update(self.create_recommendations_panel(metrics))
        layout["footer"].update(self.create_footer_panel(metrics))
        
        return layout
    
    def create_header_panel(self) -> Panel:
        """Create header panel."""
        uptime = timedelta(seconds=int(time.time() - self.start_time))
        header_text = Text()
        header_text.append("🔥 Zeus-Miner Advanced Performance Monitor ", style="bold red")
        header_text.append(f"| Uptime: {uptime} ", style="green")
        header_text.append("| 🎯 TARGET: TOP 5 RANKINGS", style="bold yellow")
        
        return Panel(
            Align.center(header_text),
            style="bright_blue",
            title="Zeus-Miner Dashboard"
        )
    
    def create_ranking_panel(self, metrics: Dict) -> Panel:
        """Create ranking status panel."""
        ranking = metrics.get('ranking', {})
        
        table = Table(show_header=False, box=None)
        table.add_column(style="cyan")
        table.add_column(style="white")
        
        position = ranking.get('current_position', 'N/A')
        target = ranking.get('target_position', 5)
        trend = ranking.get('trend', 'unknown')
        score = ranking.get('score', 0)
        gap = ranking.get('gap_to_top5', 0)
        
        # Color code based on position
        if position <= 5:
            pos_style = "bold green"
        elif position <= 10:
            pos_style = "yellow"
        else:
            pos_style = "red"
        
        table.add_row("Current Rank:", f"[{pos_style}]#{position}[/]")
        table.add_row("Target Rank:", f"[bold green]#{target}[/]")
        table.add_row("Trend:", f"[{'green' if trend == 'improving' else 'yellow' if trend == 'stable' else 'red'}]{trend}[/]")
        table.add_row("Score:", f"[white]{score:.3f}[/]")
        table.add_row("Gap to Top 5:", f"[yellow]{gap:.3f}[/]")
        
        return Panel(table, title="🏆 Ranking Status", border_style="yellow")
    
    def create_performance_panel(self, metrics: Dict) -> Panel:
        """Create performance metrics panel."""
        perf = metrics.get('performance', {})
        
        table = Table(show_header=False, box=None)
        table.add_column(style="cyan")
        table.add_column(style="white")
        table.add_column(style="dim")
        
        success_rate = perf.get('success_rate', 0)
        response_time = perf.get('avg_response_time', 0)
        hashrate = perf.get('hashrate', 0)
        efficiency = perf.get('efficiency', 0)
        uptime = perf.get('uptime', 0)
        
        # Color code based on targets
        success_color = "green" if success_rate >= 0.95 else "yellow" if success_rate >= 0.90 else "red"
        time_color = "green" if response_time <= 3000 else "yellow" if response_time <= 4000 else "red"
        efficiency_color = "green" if efficiency >= 0.95 else "yellow" if efficiency >= 0.90 else "red"
        
        table.add_row("Success Rate:", f"[{success_color}]{success_rate:.1%}[/]", f"(target: 95%)")
        table.add_row("Response Time:", f"[{time_color}]{response_time:.0f}ms[/]", f"(target: <3000ms)")
        table.add_row("Hashrate:", f"[white]{hashrate:.0f} KH/s[/]", "")
        table.add_row("Efficiency:", f"[{efficiency_color}]{efficiency:.1%}[/]", f"(target: 98%)")
        table.add_row("Uptime:", f"[green]{uptime:.1%}[/]", f"(target: 99.5%)")
        
        return Panel(table, title="⚡ Performance Metrics", border_style="green")
    
    def create_hardware_panel(self, metrics: Dict) -> Panel:
        """Create hardware status panel."""
        hardware = metrics.get('hardware', {})
        
        table = Table(show_header=False, box=None)
        table.add_column(style="cyan")
        table.add_column(style="white")
        
        temp = hardware.get('temperature', 0)
        freq = hardware.get('frequency', 0)
        power = hardware.get('power_usage', 0)
        fan_speed = hardware.get('fan_speed', 0)
        
        # Color code temperature
        temp_color = "green" if temp < 70 else "yellow" if temp < 80 else "red"
        
        table.add_row("Temperature:", f"[{temp_color}]{temp:.1f}°C[/]")
        table.add_row("Frequency:", f"[white]{freq} MHz[/]")
        table.add_row("Power Usage:", f"[white]{power:.1f}W[/]")
        table.add_row("Fan Speed:", f"[white]{fan_speed} RPM[/]")
        table.add_row("Status:", f"[green]{hardware.get('health_status', 'unknown')}[/]")
        
        return Panel(table, title="🔧 Hardware Status", border_style="blue")
    
    def create_trends_panel(self, metrics: Dict) -> Panel:
        """Create trends analysis panel."""
        trends = self.calculate_trend_analysis()
        
        if trends.get('insufficient_data'):
            return Panel(
                "[yellow]Collecting trend data...[/]",
                title="📈 Performance Trends",
                border_style="yellow"
            )
        
        table = Table(show_header=True, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Change", style="white")
        table.add_column("Direction", style="white")
        
        for metric, data in trends.items():
            change = data['change_percent']
            direction = data['direction']
            
            change_color = "green" if change > 0 else "red" if change < 0 else "yellow"
            direction_color = "green" if direction == 'improving' else "red" if direction == 'declining' else "yellow"
            
            table.add_row(
                metric.replace('_', ' ').title(),
                f"[{change_color}]{change:+.1f}%[/]",
                f"[{direction_color}]{direction}[/]"
            )
        
        return Panel(table, title="📈 Performance Trends", border_style="magenta")
    
    def create_recommendations_panel(self, metrics: Dict) -> Panel:
        """Create optimization recommendations panel."""
        recommendations = self.generate_optimization_recommendations(metrics)
        
        if not recommendations:
            return Panel(
                "[green]All systems optimal! 🎯[/]",
                title="💡 Optimization Recommendations",
                border_style="green"
            )
        
        content = ""
        for i, rec in enumerate(recommendations[:5], 1):  # Show top 5 recommendations
            priority = rec['priority']
            priority_color = "red" if priority == 'critical' else "yellow" if priority == 'high' else "blue"
            
            content += f"[{priority_color}]{i}. {rec['title']}[/] ([{priority_color}]{priority}[/])\n"
            content += f"   {rec['description']}\n"
            
            for action in rec['actions'][:2]:  # Show first 2 actions
                content += f"   • {action}\n"
            
            if i < len(recommendations):
                content += "\n"
        
        return Panel(content, title="💡 Optimization Recommendations", border_style="cyan")
    
    def create_footer_panel(self, metrics: Dict) -> Panel:
        """Create footer panel with economics and status."""
        economics = metrics.get('economics', {})
        
        footer_text = Text()
        footer_text.append("💰 Today: ", style="cyan")
        footer_text.append(f"{economics.get('tao_earned_today', 0):.4f} TAO ", style="green")
        footer_text.append("| 📊 Projected: ", style="cyan")
        footer_text.append(f"{economics.get('projected_daily', 0):.4f} TAO ", style="yellow")
        footer_text.append("| 🚀 Status: ", style="cyan")
        footer_text.append("OPTIMIZING FOR TOP 5", style="bold red")
        
        return Panel(
            Align.center(footer_text),
            style="bright_black"
        )
    
    def print_simple_dashboard(self, metrics: Dict):
        """Print simple text dashboard when Rich is not available."""
        print("\n" + "="*60)
        print("🔥 ZEUS-MINER PERFORMANCE DASHBOARD")
        print("="*60)
        
        ranking = metrics.get('ranking', {})
        perf = metrics.get('performance', {})
        hardware = metrics.get('hardware', {})
        
        print(f"\n🏆 RANKING STATUS:")
        print(f"   Current Position: #{ranking.get('current_position', 'N/A')}")
        print(f"   Target Position: #{ranking.get('target_position', 5)}")
        print(f"   Trend: {ranking.get('trend', 'unknown')}")
        print(f"   Score: {ranking.get('score', 0):.3f}")
        
        print(f"\n⚡ PERFORMANCE:")
        print(f"   Success Rate: {perf.get('success_rate', 0):.1%}")
        print(f"   Response Time: {perf.get('avg_response_time', 0):.0f}ms")
        print(f"   Hashrate: {perf.get('hashrate', 0):.0f} KH/s")
        print(f"   Efficiency: {perf.get('efficiency', 0):.1%}")
        
        print(f"\n🔧 HARDWARE:")
        print(f"   Temperature: {hardware.get('temperature', 0):.1f}°C")
        print(f"   Frequency: {hardware.get('frequency', 0)} MHz")
        print(f"   Status: {hardware.get('health_status', 'unknown')}")
        
        recommendations = self.generate_optimization_recommendations(metrics)
        if recommendations:
            print(f"\n💡 TOP RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"   {i}. {rec['title']} ({rec['priority']})")
        
        print("\n" + "="*60)
        print("🎯 TARGET: TOP 5 RANKINGS | 🚀 OPTIMIZING...")
        print("="*60)
    
    async def monitor_continuous(self, update_interval: int = 5):
        """Run continuous monitoring with live dashboard."""
        if RICH_AVAILABLE:
            with Live(self.create_dashboard_layout({}), refresh_per_second=1) as live:
                while True:
                    try:
                        metrics = self.get_current_metrics()
                        layout = self.create_dashboard_layout(metrics)
                        live.update(layout)
                        await asyncio.sleep(update_interval)
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        self.console.print(f"[red]Error in monitoring: {e}[/]")
                        await asyncio.sleep(1)
        else:
            # Simple monitoring loop
            while True:
                try:
                    metrics = self.get_current_metrics()
                    self.print_simple_dashboard(metrics)
                    await asyncio.sleep(update_interval)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error in monitoring: {e}")
                    await asyncio.sleep(1)


def main():
    """Main monitoring execution."""
    if RICH_AVAILABLE:
        console = Console()
        console.print("[bold green]🔥 Zeus-Miner Advanced Performance Monitor[/]")
        console.print("[cyan]Starting real-time dashboard...[/]")
    else:
        print("🔥 Zeus-Miner Advanced Performance Monitor")
        print("Starting monitoring...")
    
    monitor = AdvancedMonitor()
    
    try:
        asyncio.run(monitor.monitor_continuous())
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n[yellow]⏹️  Monitoring stopped by user[/]")
        else:
            print("\n⏹️  Monitoring stopped by user")


if __name__ == "__main__":
    main()