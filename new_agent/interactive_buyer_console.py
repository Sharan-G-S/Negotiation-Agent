"""
Interactive Buyer Agent Console
Where the agent represents the USER (buyer) and you input seller responses manually
"""

import asyncio
import os
from typing import Dict, Any
from datetime import datetime

# Rich console imports
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.layout import Layout
    from rich.rule import Rule
    from rich import box
    from rich.columns import Columns
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .buyer_agent import BuyerNegotiationAgent, BuyerPersonality, NegotiationPhase

class InteractiveBuyerConsole:
    """Interactive console for buyer negotiation agent"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.agent = None
        
        # Default configuration
        self.config = {
            "product": "iPhone 13 Pro",
            "target_price": 75000,
            "max_budget": 85000,
            "personality": BuyerPersonality.VALUE_SEEKER,
            "currency": "INR"
        }
        
        # Session state
        self.current_seller = "Online Seller"
        self.negotiation_active = False
    
    async def initialize(self):
        """Initialize the buyer agent"""
        if self.console:
            self.console.print(Panel.fit(
                "[bold green]🛒 Initializing Buyer Negotiation Agent...[/bold green]",
                box=box.DOUBLE
            ))
        else:
            print("🛒 Initializing Buyer Negotiation Agent...")
        
        # Get API key
        api_key = os.getenv('GOOGLE_API_KEY', 'mock')
        self.agent = BuyerNegotiationAgent(api_key=api_key, personality=self.config["personality"])
        
        if self.console:
            self.console.print("✅ [green]Agent initialized successfully![/green]")
        else:
            print("✅ Agent initialized successfully!")
    
    def display_main_menu(self):
        """Display the main menu"""
        if not self.console:
            print("\n=== Buyer Negotiation Agent ===")
            print("1. Configure Settings")
            print("2. Find Online Sellers")
            print("3. Start Negotiation")
            print("4. View Help")
            print("5. Exit")
            return
        
        title = Text("🛒 Buyer Negotiation Agent", style="bold green", justify="center")
        
        # Main menu
        menu_table = Table(box=box.ROUNDED, show_header=False)
        menu_table.add_column("Option", style="cyan", width=6)
        menu_table.add_column("Description", style="white")
        
        menu_table.add_row("1", "⚙️ Configure Settings")
        menu_table.add_row("2", "🔍 Find Online Sellers")
        menu_table.add_row("3", "💬 Start Negotiation")
        menu_table.add_row("4", "❓ Help & Guide")
        menu_table.add_row("5", "🚪 Exit")
        
        # Current settings
        settings_table = Table(box=box.SIMPLE, show_header=False, title="Current Settings")
        settings_table.add_column("Setting", style="yellow")
        settings_table.add_column("Value", style="green")
        
        settings_table.add_row("Product", self.config["product"])
        settings_table.add_row("Target Price", f"₹{self.config['target_price']:,}")
        settings_table.add_row("Max Budget", f"₹{self.config['max_budget']:,}")
        settings_table.add_row("Personality", self.config["personality"].replace("_", " ").title())
        settings_table.add_row("Currency", self.config["currency"])
        
        layout = Layout()
        layout.split_row(
            Layout(Panel(menu_table, title="Main Menu"), name="menu"),
            Layout(Panel(settings_table), name="settings")
        )
        
        self.console.print(Panel(title))
        self.console.print(layout)
    
    async def configure_settings(self):
        """Configure agent settings"""
        if not self.console:
            return await self._simple_configure()
        
        self.console.print(Rule("[bold blue]⚙️ Configuration[/bold blue]"))
        
        # Product configuration
        self.config["product"] = Prompt.ask("Product to buy", default=self.config["product"])
        
        # Pricing configuration
        self.config["target_price"] = IntPrompt.ask("Target price (₹)", default=self.config["target_price"])
        self.config["max_budget"] = IntPrompt.ask("Maximum budget (₹)", default=self.config["max_budget"])
        
        # Personality selection
        personality_table = Table(box=box.ROUNDED)
        personality_table.add_column("Option", style="cyan")
        personality_table.add_column("Personality", style="yellow")
        personality_table.add_column("Description", style="white")
        
        personalities = [
            ("1", "Budget Conscious", "Focuses on getting the lowest price possible"),
            ("2", "Value Seeker", "Wants the best value for money (recommended)"),
            ("3", "Time Saver", "Makes quick decisions at fair prices"),
            ("4", "Quality Focused", "Willing to pay more for better quality"),
            ("5", "Aggressive Bargainer", "Pushes hard for maximum discounts"),
            ("6", "Diplomatic Negotiator", "Polite but firm in negotiations")
        ]
        
        for option, name, desc in personalities:
            current = " (current)" if name.lower().replace(" ", "_") == self.config["personality"] else ""
            personality_table.add_row(option, f"{name}{current}", desc)
        
        self.console.print(Panel(personality_table, title="🎭 Choose Buyer Personality"))
        
        personality_choice = Prompt.ask("Select personality", choices=[str(i) for i in range(1, 7)], default="2")
        personality_map = {
            "1": BuyerPersonality.BUDGET_CONSCIOUS,
            "2": BuyerPersonality.VALUE_SEEKER,
            "3": BuyerPersonality.TIME_SAVER,
            "4": BuyerPersonality.QUALITY_FOCUSED,
            "5": BuyerPersonality.AGGRESSIVE_BARGAINER,
            "6": BuyerPersonality.DIPLOMATIC_NEGOTIATOR
        }
        self.config["personality"] = personality_map[personality_choice]
        
        # Reinitialize agent with new personality
        api_key = os.getenv('GOOGLE_API_KEY', 'mock')
        self.agent = BuyerNegotiationAgent(api_key=api_key, personality=self.config["personality"])
        
        self.console.print("✅ [green]Settings updated![/green]")
        await asyncio.sleep(1)
    
    async def _simple_configure(self):
        """Simple configuration for non-rich mode"""
        print("\n=== Configuration ===")
        product = input(f"Product ({self.config['product']}): ").strip()
        if product:
            self.config["product"] = product
        
        try:
            target = input(f"Target price ({self.config['target_price']}): ").strip()
            if target:
                self.config["target_price"] = int(target)
            
            budget = input(f"Max budget ({self.config['max_budget']}): ").strip()
            if budget:
                self.config["max_budget"] = int(budget)
        except ValueError:
            print("Invalid number format. Using current values.")
        
        print("Personalities: 1-Budget Conscious, 2-Value Seeker, 3-Time Saver")
        print("              4-Quality Focused, 5-Aggressive, 6-Diplomatic")
        choice = input("Select personality (1-6): ").strip()
        
        personality_map = {
            "1": BuyerPersonality.BUDGET_CONSCIOUS,
            "2": BuyerPersonality.VALUE_SEEKER,
            "3": BuyerPersonality.TIME_SAVER,
            "4": BuyerPersonality.QUALITY_FOCUSED,
            "5": BuyerPersonality.AGGRESSIVE_BARGAINER,
            "6": BuyerPersonality.DIPLOMATIC_NEGOTIATOR
        }
        
        if choice in personality_map:
            self.config["personality"] = personality_map[choice]
            # Reinitialize agent
            api_key = os.getenv('GOOGLE_API_KEY', 'mock')
            self.agent = BuyerNegotiationAgent(api_key=api_key, personality=self.config["personality"])
    
    def find_sellers(self):
        """Find and display online sellers"""
        if not self.console:
            print("\n🔍 Finding sellers online...")
            sellers_info = self.agent.find_sellers()
            print(sellers_info)
            return
        
        self.console.print(Rule("[bold blue]🔍 Finding Online Sellers[/bold blue]"))
        
        with self.console.status("[spinner dots] Searching online marketplaces..."):
            sellers_info = self.agent.find_sellers()
        
        # Display sellers in a nice format
        lines = sellers_info.split('\n')
        sellers_panel = Panel(
            Text(sellers_info, style="white"),
            title="🛒 Available Sellers",
            border_style="green"
        )
        
        self.console.print(sellers_panel)
        
        if Confirm.ask("\nDo you want to start negotiating with one of these sellers?"):
            self.current_seller = Prompt.ask("Enter seller name", default="TechMart Electronics")
            return True
        
        return False
    
    async def start_negotiation(self):
        """Start the negotiation process"""
        if not self.console:
            return await self._simple_negotiation()
        
        self.console.print(Rule("[bold green]💬 Starting Negotiation[/bold green]"))
        
        # Initialize negotiation
        start_msg = self.agent.start_negotiation(
            self.config["product"],
            self.config["target_price"],
            self.config["max_budget"]
        )
        
        setup_panel = Panel(
            Text(start_msg, style="green"),
            title="🚀 Negotiation Setup",
            border_style="green"
        )
        self.console.print(setup_panel)
        
        self.negotiation_active = True
        await self._negotiation_loop()
    
    async def _negotiation_loop(self):
        """Main negotiation conversation loop"""
        round_count = 0
        
        instruction_panel = Panel(
            Text("You will input the seller's messages manually.\n"
                 "The agent will respond as a buyer trying to get the best deal.\n"
                 "Commands: /help, /analysis, /summary, /quit", 
                 style="yellow"),
            title="📝 Instructions",
            border_style="yellow"
        )
        self.console.print(instruction_panel)
        
        while self.negotiation_active:
            try:
                round_count += 1
                
                # Get seller input
                self.console.print(f"\n[bold blue]Round {round_count}[/bold blue]")
                
                if round_count == 1:
                    seller_input = Prompt.ask(
                        f"[blue]💼 {self.current_seller} says",
                        default="Hi! I have the item you're looking for. Price is ₹85,000."
                    )
                else:
                    seller_input = Prompt.ask(f"[blue]💼 {self.current_seller} says")
                
                if seller_input.startswith('/'):
                    if await self._handle_command(seller_input):
                        continue
                    else:
                        break
                
                # Get buyer's response
                self.console.print("\n[yellow]🛒 Buyer is analyzing and responding...[/yellow]")
                
                with self.console.status("[spinner dots] Generating response..."):
                    response_data = self.agent.get_buyer_response(seller_input, self.current_seller)
                
                # Display buyer's response
                self._display_buyer_response(response_data, round_count)
                
                # Check for deal closure
                if "deal" in seller_input.lower() and "final" in seller_input.lower():
                    if Confirm.ask("\n🤝 Accept this deal?"):
                        self.console.print("✅ [green]Deal accepted! Negotiation completed.[/green]")
                        break
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Negotiation paused. Type /quit to exit.[/yellow]")
                continue
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
                continue
        
        # Show final summary
        await self._show_final_summary()
    
    def _display_buyer_response(self, response_data: Dict[str, Any], round_count: int):
        """Display the buyer's response with analysis"""
        if not self.console:
            print(f"🛒 Buyer: {response_data['response']}")
            print(f"Status: {response_data['negotiation_status']}")
            return
        
        # Main response panel
        response_panel = Panel(
            Text(response_data['response'], style="white"),
            title="🛒 Buyer Response",
            border_style="blue"
        )
        
        # Analysis panel
        analysis = response_data['analysis']
        analysis_table = Table(box=box.SIMPLE, show_header=False)
        analysis_table.add_column("Metric", style="cyan")
        analysis_table.add_column("Value", style="yellow")
        
        analysis_table.add_row("Phase", analysis['phase'].replace('_', ' ').title())
        analysis_table.add_row("Round", str(analysis['round']))
        
        if analysis['seller_price'] > 0:
            analysis_table.add_row("Seller Price", f"₹{analysis['seller_price']:,}")
            analysis_table.add_row("Target Price", f"₹{analysis['target_price']:,}")
            analysis_table.add_row("Difference", f"₹{analysis['price_difference']:,}")
        
        analysis_table.add_row("Status", response_data['negotiation_status'])
        
        # Layout
        layout = Layout()
        layout.split_column(
            Layout(response_panel, size=4),
            Layout(Panel(analysis_table, title="📊 Analysis"), size=6)
        )
        
        self.console.print(layout)
        
        # Show tactics if round > 1
        if round_count > 1 and response_data.get('tactics'):
            tactics_panel = Panel(
                Text(response_data['tactics'], style="green"),
                title="🎯 Recommended Tactics",
                border_style="green"
            )
            self.console.print(tactics_panel)
    
    async def _handle_command(self, command: str) -> bool:
        """Handle special commands"""
        if command == '/quit':
            self.negotiation_active = False
            return False
        elif command == '/help':
            await self._show_help()
        elif command == '/analysis':
            await self._show_analysis()
        elif command == '/summary':
            await self._show_summary()
        return True
    
    async def _show_help(self):
        """Show help information"""
        help_text = """
[bold]Available Commands:[/bold]
• [cyan]/help[/cyan] - Show this help
• [cyan]/analysis[/cyan] - Show price analysis
• [cyan]/summary[/cyan] - Show negotiation summary
• [cyan]/quit[/cyan] - End negotiation

[bold]How it works:[/bold]
• You represent the SELLER - input their messages
• The agent represents YOU as the BUYER
• The agent will try to negotiate the best price
• Watch the tactics and use them for real negotiations!

[bold]Tips for seller messages:[/bold]
• Include prices: "Price is ₹85,000"
• Show flexibility: "Best I can do is ₹80,000"
• Create urgency: "This is my final offer"
• Mention competition: "I have other buyers"
        """
        
        if self.console:
            self.console.print(Panel(help_text.strip(), title="❓ Help"))
        else:
            print(help_text)
    
    async def _show_analysis(self):
        """Show current price analysis"""
        if self.agent.current_negotiation["seller_price"] > 0:
            from .buyer_agent import PriceComparisonTool
            price_tool = PriceComparisonTool()
            analysis = price_tool._run(
                str(self.agent.current_negotiation["seller_price"]),
                str(self.agent.current_negotiation["target_price"]),
                self.agent.current_negotiation["product"]
            )
            
            if self.console:
                self.console.print(Panel(Text(analysis, style="white"), title="📈 Price Analysis"))
            else:
                print("📈 Price Analysis:")
                print(analysis)
        else:
            msg = "No price information available yet."
            if self.console:
                self.console.print(f"[yellow]{msg}[/yellow]")
            else:
                print(msg)
    
    async def _show_summary(self):
        """Show negotiation summary"""
        summary = self.agent.get_negotiation_summary()
        
        if not self.console:
            print("\n📋 Negotiation Summary:")
            print(f"Product: {summary['product']}")
            print(f"Target: ₹{summary['target_price']:,}")
            print(f"Current Price: ₹{summary['seller_price']:,}")
            print(f"Rounds: {summary['total_rounds']}")
            return
        
        summary_table = Table(box=box.ROUNDED, title="📋 Negotiation Summary")
        summary_table.add_column("Item", style="cyan")
        summary_table.add_column("Value", style="yellow")
        
        summary_table.add_row("Product", summary['product'])
        summary_table.add_row("Target Price", f"₹{summary['target_price']:,}")
        summary_table.add_row("Current Price", f"₹{summary['seller_price']:,}")
        summary_table.add_row("Potential Savings", f"₹{summary['savings_potential']:,}")
        summary_table.add_row("Total Rounds", str(summary['total_rounds']))
        summary_table.add_row("Status", summary['negotiation_status'])
        
        self.console.print(summary_table)
    
    async def _show_final_summary(self):
        """Show final negotiation summary"""
        if self.console:
            self.console.print(Rule("[bold green]🏁 Negotiation Complete[/bold green]"))
        else:
            print("\n🏁 Negotiation Complete")
        
        await self._show_summary()
    
    async def _simple_negotiation(self):
        """Simple negotiation for non-rich mode"""
        print(f"\n💬 Starting negotiation for: {self.config['product']}")
        print(f"Target: ₹{self.config['target_price']:,} | Max: ₹{self.config['max_budget']:,}")
        print("Type '/quit' to exit\n")
        
        round_count = 0
        self.negotiation_active = True
        
        while self.negotiation_active:
            try:
                round_count += 1
                print(f"\nRound {round_count}")
                
                seller_input = input("💼 Seller says: ").strip()
                
                if seller_input == '/quit':
                    break
                
                print("🛒 Buyer is thinking...")
                response_data = self.agent.get_buyer_response(seller_input, self.current_seller)
                
                print(f"🛒 Buyer: {response_data['response']}")
                print(f"Status: {response_data['negotiation_status']}")
                
                if round_count > 1:
                    print(f"Phase: {response_data['analysis']['phase']}")
                
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
                    await self.configure_settings()
                elif choice == "2":
                    self.find_sellers()
                elif choice == "3":
                    await self.start_negotiation()
                elif choice == "4":
                    await self._show_help()
                elif choice == "5":
                    break
                
                if self.console and choice != "3":  # Don't pause after negotiation
                    Prompt.ask("\nPress Enter to continue", default="")
                    self.console.clear()
                
            except KeyboardInterrupt:
                if self.console:
                    self.console.print("\n[yellow]Goodbye! Happy negotiating! 🛒[/yellow]")
                else:
                    print("\nGoodbye! Happy negotiating! 🛒")
                break
            except Exception as e:
                if self.console:
                    self.console.print(f"[red]Error: {str(e)}[/red]")
                else:
                    print(f"Error: {str(e)}")

# Main entry point
async def main():
    """Run the interactive buyer console"""
    console = InteractiveBuyerConsole()
    await console.run()

if __name__ == "__main__":
    asyncio.run(main())