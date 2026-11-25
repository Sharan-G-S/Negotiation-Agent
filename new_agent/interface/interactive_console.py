"""
Interactive Console Interface for Negotiation Agent
Rich console interface with tone control, real-time feedback, and comprehensive settings
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

# Rich console imports for beautiful UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.layout import Layout
    from rich.text import Text
    from rich.prompt import Prompt, Confirm, IntPrompt, FloatPrompt
    from rich.columns import Columns
    from rich.live import Live
    from rich.align import Align
    from rich.rule import Rule
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Warning: Rich library not available. Install with: pip install rich")

from ..core.agent import NegotiationAgent
from ..mcp.server import NegotiationMCPServer
from ..intelligence.strategy import NegotiationIntelligenceEngine, NegotiationPhase, NegotiationTactic

class NegotiationTone(str, Enum):
    """Available negotiation tones"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AGGRESSIVE = "aggressive"
    DIPLOMATIC = "diplomatic"
    CASUAL = "casual"
    FORMAL = "formal"
    PERSUASIVE = "persuasive"
    ANALYTICAL = "analytical"

class InteractiveNegotiationConsole:
    """Enhanced interactive console interface for negotiation agent"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.agent = None
        self.mcp_server = None
        self.intelligence_engine = None
        self.current_session = None
        
        # Configuration
        self.config = {
            "tone": NegotiationTone.PROFESSIONAL,
            "target_price": 500,
            "max_price": 800,
            "product": "iPhone 13 Pro",
            "preferred_tactics": [
                NegotiationTactic.ANCHORING,
                NegotiationTactic.RECIPROCITY,
                NegotiationTactic.COMPROMISE
            ],
            "aggressiveness": 0.5,  # 0-1 scale
            "patience": 0.7,        # 0-1 scale
            "risk_tolerance": 0.4,  # 0-1 scale
            "show_analytics": True,
            "auto_suggest": True,
            "debug_mode": False
        }
        
        # Session state
        self.negotiation_history = []
        self.current_phase = NegotiationPhase.GREETING
        self.round_count = 0
        self.price_progression = []
        
    async def initialize(self):
        """Initialize all components"""
        if self.console:
            self.console.print(Panel.fit(
                "[bold blue]🚀 Initializing AI Negotiation Agent...[/bold blue]",
                box=box.DOUBLE
            ))
        
        # Get API key from environment or user
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            if self.console:
                self.console.print("[yellow]⚠️ No GOOGLE_API_KEY found in environment[/yellow]")
                api_key = Prompt.ask("Enter your Google Gemini API key (or press Enter to use mock responses)", default="mock")
            else:
                print("⚠️ No GOOGLE_API_KEY found in environment")
                api_key = input("Enter your Google Gemini API key (or press Enter to use mock responses): ").strip() or "mock"
        
        # Initialize components
        self.agent = NegotiationAgent(api_key=api_key)
        self.mcp_server = NegotiationMCPServer()
        self.intelligence_engine = NegotiationIntelligenceEngine()
        
        # Create new session
        session_data = {
            "product": self.config["product"],
            "target_price": self.config["target_price"],
            "max_price": self.config["max_price"],
            "user_id": "interactive_user",
            "tone": self.config["tone"]
        }
        
        self.current_session = await self.mcp_server.create_session(session_data)
        
        if self.console:
            self.console.print(f"✅ Session created: [green]{self.current_session}[/green]")
        else:
            print(f"✅ Session created: {self.current_session}")
    
    def display_main_menu(self):
        """Display the main menu"""
        if not self.console:
            print("\n=== AI Negotiation Agent - Interactive Mode ===")
            print("1. Start New Negotiation")
            print("2. Configure Settings")
            print("3. View Analytics")
            print("4. Help")
            print("5. Exit")
            return
        
        # Rich interface
        title = Text("🤖 AI Negotiation Agent", style="bold blue", justify="center")
        
        menu_table = Table(box=box.ROUNDED, show_header=False)
        menu_table.add_column("Option", style="cyan", width=6)
        menu_table.add_column("Description", style="white")
        
        menu_table.add_row("1", "🚀 Start New Negotiation")
        menu_table.add_row("2", "⚙️  Configure Settings") 
        menu_table.add_row("3", "📊 View Analytics")
        menu_table.add_row("4", "❓ Help & Tips")
        menu_table.add_row("5", "🚪 Exit")
        
        # Current settings panel
        settings_table = Table(box=box.SIMPLE, show_header=False)
        settings_table.add_column("Setting", style="yellow")
        settings_table.add_column("Value", style="green")
        
        settings_table.add_row("Tone", self.config["tone"].title())
        settings_table.add_row("Target Price", f"${self.config['target_price']}")
        settings_table.add_row("Max Price", f"${self.config['max_price']}")
        settings_table.add_row("Product", self.config["product"])
        
        layout = Layout()
        layout.split_row(
            Layout(Panel(menu_table, title="Main Menu"), name="menu"),
            Layout(Panel(settings_table, title="Current Settings"), name="settings")
        )
        
        self.console.print(Panel(title))
        self.console.print(layout)
    
    async def configure_settings(self):
        """Interactive settings configuration"""
        if not self.console:
            print("\n=== Configuration ===")
            return await self.simple_configure_settings()
        
        self.console.print(Rule("[bold blue]Configuration[/bold blue]"))
        
        # Tone selection
        tone_table = Table(box=box.ROUNDED)
        tone_table.add_column("Option", style="cyan")
        tone_table.add_column("Tone", style="yellow")
        tone_table.add_column("Description", style="white")
        
        tones = [
            ("1", "Professional", "Formal, business-like approach"),
            ("2", "Friendly", "Warm, relationship-focused"),
            ("3", "Aggressive", "Direct, assertive, high-pressure"),
            ("4", "Diplomatic", "Tactful, measured responses"),
            ("5", "Casual", "Relaxed, informal style"),
            ("6", "Persuasive", "Influence-focused, compelling"),
            ("7", "Analytical", "Data-driven, logical approach")
        ]
        
        for option, tone, desc in tones:
            style = "green" if tone.lower() == self.config["tone"] else "white"
            tone_table.add_row(option, f"[{style}]{tone}[/{style}]", desc)
        
        self.console.print(Panel(tone_table, title="🎭 Select Negotiation Tone"))
        
        tone_choice = Prompt.ask("Choose tone", choices=[str(i) for i in range(1, 8)], default="1")
        tone_map = {
            "1": NegotiationTone.PROFESSIONAL,
            "2": NegotiationTone.FRIENDLY,
            "3": NegotiationTone.AGGRESSIVE,
            "4": NegotiationTone.DIPLOMATIC,
            "5": NegotiationTone.CASUAL,
            "6": NegotiationTone.PERSUASIVE,
            "7": NegotiationTone.ANALYTICAL
        }
        self.config["tone"] = tone_map[tone_choice]
        
        # Product and pricing
        self.config["product"] = Prompt.ask("Product name", default=self.config["product"])
        self.config["target_price"] = IntPrompt.ask("Target price ($)", default=self.config["target_price"])
        self.config["max_price"] = IntPrompt.ask("Maximum price ($)", default=self.config["max_price"])
        
        # Advanced settings
        if Confirm.ask("Configure advanced settings?", default=False):
            self.config["aggressiveness"] = FloatPrompt.ask(
                "Aggressiveness (0.0-1.0)", 
                default=self.config["aggressiveness"],
                min_value=0.0, max_value=1.0
            )
            self.config["patience"] = FloatPrompt.ask(
                "Patience level (0.0-1.0)", 
                default=self.config["patience"],
                min_value=0.0, max_value=1.0
            )
            self.config["risk_tolerance"] = FloatPrompt.ask(
                "Risk tolerance (0.0-1.0)", 
                default=self.config["risk_tolerance"],
                min_value=0.0, max_value=1.0
            )
        
        self.console.print("✅ [green]Settings saved![/green]")
        await asyncio.sleep(1)
    
    async def simple_configure_settings(self):
        """Simple settings configuration for non-rich mode"""
        print("\n=== Tone Selection ===")
        tones = [
            ("1", "Professional"), ("2", "Friendly"), ("3", "Aggressive"), 
            ("4", "Diplomatic"), ("5", "Casual"), ("6", "Persuasive"), ("7", "Analytical")
        ]
        
        for option, tone in tones:
            current = " (current)" if tone.lower() == self.config["tone"] else ""
            print(f"{option}. {tone}{current}")
        
        choice = input("Select tone (1-7): ").strip()
        if choice in ["1", "2", "3", "4", "5", "6", "7"]:
            tone_map = {
                "1": NegotiationTone.PROFESSIONAL, "2": NegotiationTone.FRIENDLY,
                "3": NegotiationTone.AGGRESSIVE, "4": NegotiationTone.DIPLOMATIC,
                "5": NegotiationTone.CASUAL, "6": NegotiationTone.PERSUASIVE,
                "7": NegotiationTone.ANALYTICAL
            }
            self.config["tone"] = tone_map[choice]
        
        product = input(f"Product name ({self.config['product']}): ").strip()
        if product:
            self.config["product"] = product
        
        try:
            target = input(f"Target price ({self.config['target_price']}): ").strip()
            if target:
                self.config["target_price"] = int(target)
            
            max_price = input(f"Max price ({self.config['max_price']}): ").strip()
            if max_price:
                self.config["max_price"] = int(max_price)
        except ValueError:
            print("Invalid price format. Using current values.")
    
    async def start_negotiation(self):
        """Start interactive negotiation"""
        if not self.console:
            return await self.simple_negotiation()
        
        self.console.print(Rule("[bold green]🚀 Starting Negotiation[/bold green]"))
        
        # Display negotiation setup
        setup_table = Table(box=box.ROUNDED, title="Negotiation Setup")
        setup_table.add_column("Parameter", style="yellow")
        setup_table.add_column("Value", style="green")
        
        setup_table.add_row("Product", self.config["product"])
        setup_table.add_row("Target Price", f"${self.config['target_price']}")
        setup_table.add_row("Maximum Price", f"${self.config['max_price']}")
        setup_table.add_row("Tone", self.config["tone"].title())
        setup_table.add_row("Session ID", self.current_session)
        
        self.console.print(setup_table)
        self.console.print()
        
        # Start negotiation loop
        await self.negotiation_loop()
    
    async def negotiation_loop(self):
        """Main negotiation interaction loop"""
        self.console.print(Panel.fit(
            "[bold yellow]💬 Negotiation Started - Type your messages below\n"
            "Commands: /help, /settings, /analytics, /quit[/bold yellow]"
        ))
        
        while True:
            try:
                # Get seller message
                self.console.print()
                seller_input = Prompt.ask("[blue]💼 Seller says", default="Hi! I'm selling this item.")
                
                if seller_input.startswith('/'):
                    if await self.handle_command(seller_input):
                        continue
                    else:
                        break
                
                # Add to history
                self.negotiation_history.append({
                    "role": "seller",
                    "message": seller_input,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Get AI response
                self.console.print("\n[yellow]🤖 Agent is thinking...[/yellow]")
                
                with self.console.status("[spinner dots] Analyzing and responding..."):
                    # Update session context
                    await self.mcp_server.update_context(
                        self.current_session,
                        {"seller_message": seller_input, "round": self.round_count}
                    )
                    
                    # Get agent response
                    context = {
                        "product": self.config["product"],
                        "target_price": self.config["target_price"],
                        "max_price": self.config["max_price"],
                        "tone": self.config["tone"],
                        "conversation_history": self.negotiation_history,
                        "current_phase": self.current_phase,
                        "round_count": self.round_count
                    }
                    
                    agent_response = await self.agent.get_response(seller_input, context)
                    
                    # Intelligence analysis
                    seller_analysis = await self.intelligence_engine.analyze_seller(
                        self.negotiation_history, 
                        [msg["message"] for msg in self.negotiation_history if msg["role"] == "seller"]
                    )
                    
                    tactics = await self.intelligence_engine.recommend_tactics(
                        seller_analysis, context
                    )
                
                # Display response with analytics
                self.display_agent_response(agent_response, seller_analysis, tactics)
                
                # Add to history
                self.negotiation_history.append({
                    "role": "agent",
                    "message": agent_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                self.round_count += 1
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Negotiation paused. Type /quit to exit.[/yellow]")
                continue
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
                continue
    
    def display_agent_response(self, response: str, seller_analysis, tactics):
        """Display agent response with analytics"""
        if not self.console:
            print(f"\n🤖 Agent: {response}")
            return
        
        # Main response
        response_panel = Panel(
            Text(response, style="white"),
            title="🤖 Agent Response",
            border_style="green"
        )
        
        # Analytics panels
        analysis_table = Table(box=box.SIMPLE, show_header=False)
        analysis_table.add_column("Metric", style="cyan")
        analysis_table.add_column("Value", style="yellow")
        
        analysis_table.add_row("Seller Type", seller_analysis.personality_type.title())
        analysis_table.add_row("Flexibility", f"{seller_analysis.flexibility_score:.0%}")
        analysis_table.add_row("Urgency", f"{seller_analysis.urgency_level:.0%}")
        analysis_table.add_row("Phase", self.current_phase.title())
        analysis_table.add_row("Round", str(self.round_count))
        
        # Tactics panel
        tactics_text = ""
        for i, (tactic, confidence) in enumerate(tactics[:3], 1):
            tactics_text += f"{i}. {tactic.title()} ({confidence:.0%})\n"
        
        if not tactics_text:
            tactics_text = "No specific tactics recommended"
        
        layout = Layout()
        layout.split_column(
            Layout(response_panel, size=3),
            Layout(
                Layout.split_row(
                    Layout(Panel(analysis_table, title="📊 Analysis")),
                    Layout(Panel(tactics_text.strip(), title="🎯 Recommended Tactics"))
                ),
                size=6
            )
        )
        
        self.console.print(layout)
    
    async def handle_command(self, command: str) -> bool:
        """Handle special commands. Returns True to continue, False to quit"""
        if command == '/quit':
            return False
        elif command == '/help':
            await self.show_help()
        elif command == '/settings':
            await self.configure_settings()
        elif command == '/analytics':
            await self.show_analytics()
        return True
    
    async def show_analytics(self):
        """Display negotiation analytics"""
        if not self.console:
            print("\n=== Analytics ===")
            print(f"Rounds: {self.round_count}")
            print(f"Messages: {len(self.negotiation_history)}")
            return
        
        analytics = await self.mcp_server.get_session_analytics(self.current_session)
        
        analytics_table = Table(box=box.ROUNDED, title="📊 Negotiation Analytics")
        analytics_table.add_column("Metric", style="cyan")
        analytics_table.add_column("Value", style="yellow")
        
        analytics_table.add_row("Session ID", analytics.get("session_id", "N/A"))
        analytics_table.add_row("Duration", f"{analytics.get('duration_minutes', 0):.1f} minutes")
        analytics_table.add_row("Total Messages", str(analytics.get("message_count", 0)))
        analytics_table.add_row("Rounds", str(analytics.get("negotiation_rounds", 0)))
        analytics_table.add_row("Status", analytics.get("final_outcome", "active").title())
        
        self.console.print(analytics_table)
    
    async def show_help(self):
        """Display help information"""
        if not self.console:
            print("\n=== Help ===")
            print("Commands: /help, /settings, /analytics, /quit")
            print("Type seller messages to continue negotiation")
            return
        
        help_text = """
[bold]Available Commands:[/bold]
• [cyan]/help[/cyan] - Show this help
• [cyan]/settings[/cyan] - Change configuration
• [cyan]/analytics[/cyan] - View session stats
• [cyan]/quit[/cyan] - Exit negotiation

[bold]Tips:[/bold]
• The agent adapts to seller personality
• Try different tones in settings
• Watch the recommended tactics
• Use Ctrl+C to pause anytime
        """
        
        self.console.print(Panel(help_text.strip(), title="❓ Help & Tips"))
    
    async def simple_negotiation(self):
        """Simple negotiation for non-rich mode"""
        print(f"\n=== Negotiation Started ===")
        print(f"Product: {self.config['product']}")
        print(f"Target: ${self.config['target_price']}, Max: ${self.config['max_price']}")
        print(f"Tone: {self.config['tone'].title()}")
        print("\nType '/quit' to exit, '/help' for commands\n")
        
        while True:
            try:
                seller_input = input("\n💼 Seller says: ").strip()
                
                if seller_input == '/quit':
                    break
                elif seller_input == '/help':
                    print("Commands: /quit, /help")
                    continue
                
                # Get agent response
                print("🤖 Agent is thinking...")
                
                context = {
                    "product": self.config["product"],
                    "target_price": self.config["target_price"],
                    "max_price": self.config["max_price"],
                    "tone": self.config["tone"],
                    "conversation_history": self.negotiation_history
                }
                
                agent_response = await self.agent.get_response(seller_input, context)
                print(f"🤖 Agent: {agent_response}")
                
                self.negotiation_history.append({"role": "seller", "message": seller_input})
                self.negotiation_history.append({"role": "agent", "message": agent_response})
                self.round_count += 1
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
    
    async def run(self):
        """Main run loop"""
        await self.initialize()
        
        while True:
            try:
                self.display_main_menu()
                
                if self.console:
                    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="1")
                else:
                    choice = input("\nSelect option (1-5): ").strip()
                
                if choice == "1":
                    await self.start_negotiation()
                elif choice == "2":
                    await self.configure_settings()
                elif choice == "3":
                    await self.show_analytics()
                elif choice == "4":
                    await self.show_help()
                elif choice == "5":
                    break
                
                if self.console:
                    if choice != "1":  # Don't pause after negotiation
                        Prompt.ask("\nPress Enter to continue", default="")
                        self.console.clear()
                
            except KeyboardInterrupt:
                if self.console:
                    self.console.print("\n[yellow]Goodbye![/yellow]")
                else:
                    print("\nGoodbye!")
                break
            except Exception as e:
                if self.console:
                    self.console.print(f"[red]Error: {str(e)}[/red]")
                else:
                    print(f"Error: {str(e)}")

# Main entry point for interactive mode
async def main():
    """Run the interactive console"""
    console = InteractiveNegotiationConsole()
    await console.run()

if __name__ == "__main__":
    asyncio.run(main())