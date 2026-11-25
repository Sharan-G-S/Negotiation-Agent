"""
Advanced Negotiation Intelligence System
Implements sophisticated negotiation strategies, tactics, and decision-making
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import random
import math

class NegotiationPhase(str, Enum):
    """Negotiation phases with strategic implications"""
    GREETING = "greeting"
    RAPPORT_BUILDING = "rapport_building" 
    DISCOVERY = "discovery"
    INITIAL_POSITIONING = "initial_positioning"
    ACTIVE_NEGOTIATION = "active_negotiation"
    CONCESSION_TRADING = "concession_trading"
    CLOSING = "closing"
    AGREEMENT = "agreement"
    IMPASSE = "impasse"

class NegotiationTactic(str, Enum):
    """Advanced negotiation tactics"""
    # Positioning Tactics
    ANCHORING = "anchoring"                    # Set favorable reference point
    FRAMING = "framing"                        # Present information favorably
    BRACKETING = "bracketing"                  # Extreme position to make target seem reasonable
    
    # Pressure Tactics  
    SCARCITY = "scarcity"                      # Create urgency through limited availability
    DEADLINE_PRESSURE = "deadline_pressure"    # Use time constraints
    WALKAWAY = "walkaway"                      # Threaten to leave negotiation
    
    # Value-based Tactics
    VALUE_STACKING = "value_stacking"          # Emphasize total value proposition
    BUNDLING = "bundling"                      # Package multiple items/services
    UNBUNDLING = "unbundling"                  # Separate components for negotiation
    
    # Relationship Tactics
    RECIPROCITY = "reciprocity"                # Give to get principle
    SOCIAL_PROOF = "social_proof"              # Reference what others have done
    AUTHORITY = "authority"                    # Reference expert opinions
    LIKING = "liking"                          # Build personal connection
    
    # Strategic Tactics
    INCREMENTAL_COMMITMENT = "incremental_commitment"  # Small agreements leading to big ones
    CONTRAST_PRINCIPLE = "contrast_principle"   # Make offer seem better by comparison
    COMPROMISE = "compromise"                   # Find mutually acceptable middle ground
    PROBLEM_SOLVING = "problem_solving"         # Collaborative approach
    
    # Information Tactics
    INFORMATION_GATHERING = "information_gathering"  # Learn seller's motivations
    STRATEGIC_SILENCE = "strategic_silence"     # Use pauses for effect
    MIRRORING = "mirroring"                    # Reflect seller's communication style

class SellerPersonality(str, Enum):
    """Identified seller personality types"""
    ANALYTICAL = "analytical"      # Data-driven, logical
    DRIVER = "driver"             # Results-focused, impatient
    EXPRESSIVE = "expressive"     # Emotional, relationship-focused
    AMIABLE = "amiable"          # Friendly, relationship-oriented
    AGGRESSIVE = "aggressive"     # Pushy, high-pressure
    PASSIVE = "passive"          # Avoids conflict, indecisive
    FLEXIBLE = "flexible"        # Open to negotiation
    FIRM = "firm"               # Sticks to positions

@dataclass
class MarketIntelligence:
    """Market analysis and intelligence"""
    comparable_prices: List[float]
    average_market_price: float
    price_trend: str  # "rising", "falling", "stable"
    market_saturation: float  # 0-1 scale
    seasonal_factors: Dict[str, Any]
    demand_indicators: Dict[str, Any]
    supply_indicators: Dict[str, Any]

@dataclass
class SellerAnalysis:
    """Analysis of seller behavior and characteristics"""
    personality_type: SellerPersonality
    flexibility_score: float  # 0-1 scale
    urgency_level: float     # 0-1 scale
    price_sensitivity: float # 0-1 scale
    communication_style: str
    response_patterns: Dict[str, Any]
    negotiation_history: List[Dict]
    motivations: List[str]
    constraints: List[str]

@dataclass
class TacticEffectiveness:
    """Effectiveness metrics for negotiation tactics"""
    tactic: NegotiationTactic
    success_rate: float
    average_price_improvement: float
    seller_resistance_level: float
    context_suitability: float
    risk_level: float

class NegotiationIntelligenceEngine:
    """Advanced AI-powered negotiation intelligence"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Tactic effectiveness database
        self.tactic_effectiveness = self._initialize_tactic_effectiveness()
        
        # Seller personality patterns
        self.personality_patterns = self._initialize_personality_patterns()
        
        # Market analysis weights
        self.market_weights = {
            "price_comparison": 0.4,
            "demand_supply": 0.3,
            "seasonal": 0.2,
            "trend": 0.1
        }
        
    def _initialize_tactic_effectiveness(self) -> Dict[NegotiationTactic, TacticEffectiveness]:
        """Initialize tactic effectiveness metrics"""
        return {
            NegotiationTactic.ANCHORING: TacticEffectiveness(
                tactic=NegotiationTactic.ANCHORING,
                success_rate=0.75,
                average_price_improvement=15.0,
                seller_resistance_level=0.3,
                context_suitability=0.8,
                risk_level=0.2
            ),
            NegotiationTactic.SCARCITY: TacticEffectiveness(
                tactic=NegotiationTactic.SCARCITY,
                success_rate=0.65,
                average_price_improvement=8.0,
                seller_resistance_level=0.4,
                context_suitability=0.6,
                risk_level=0.5
            ),
            NegotiationTactic.VALUE_STACKING: TacticEffectiveness(
                tactic=NegotiationTactic.VALUE_STACKING,
                success_rate=0.70,
                average_price_improvement=12.0,
                seller_resistance_level=0.2,
                context_suitability=0.9,
                risk_level=0.1
            ),
            NegotiationTactic.RECIPROCITY: TacticEffectiveness(
                tactic=NegotiationTactic.RECIPROCITY,
                success_rate=0.80,
                average_price_improvement=10.0,
                seller_resistance_level=0.2,
                context_suitability=0.85,
                risk_level=0.15
            ),
            NegotiationTactic.COMPROMISE: TacticEffectiveness(
                tactic=NegotiationTactic.COMPROMISE,
                success_rate=0.85,
                average_price_improvement=8.0,
                seller_resistance_level=0.1,
                context_suitability=0.95,
                risk_level=0.05
            )
        }
    
    def _initialize_personality_patterns(self) -> Dict[SellerPersonality, Dict]:
        """Initialize seller personality response patterns"""
        return {
            SellerPersonality.ANALYTICAL: {
                "keywords": ["data", "research", "compare", "facts", "analysis"],
                "response_style": "detailed_logical",
                "effective_tactics": [NegotiationTactic.VALUE_STACKING, NegotiationTactic.AUTHORITY],
                "ineffective_tactics": [NegotiationTactic.SCARCITY, NegotiationTactic.DEADLINE_PRESSURE],
                "approach": "data-driven"
            },
            SellerPersonality.DRIVER: {
                "keywords": ["quick", "bottom line", "decision", "time", "efficient"],
                "response_style": "direct_brief",
                "effective_tactics": [NegotiationTactic.DEADLINE_PRESSURE, NegotiationTactic.ANCHORING],
                "ineffective_tactics": [NegotiationTactic.LIKING, NegotiationTactic.STRATEGIC_SILENCE],
                "approach": "results-focused"
            },
            SellerPersonality.EXPRESSIVE: {
                "keywords": ["feel", "exciting", "amazing", "love", "relationship"],
                "response_style": "emotional_enthusiastic",
                "effective_tactics": [NegotiationTactic.LIKING, NegotiationTactic.SOCIAL_PROOF],
                "ineffective_tactics": [NegotiationTactic.WALKAWAY, NegotiationTactic.INFORMATION_GATHERING],
                "approach": "relationship-focused"
            },
            SellerPersonality.AMIABLE: {
                "keywords": ["help", "understand", "together", "comfortable", "support"],
                "response_style": "friendly_cooperative",
                "effective_tactics": [NegotiationTactic.RECIPROCITY, NegotiationTactic.COMPROMISE],
                "ineffective_tactics": [NegotiationTactic.WALKAWAY, NegotiationTactic.DEADLINE_PRESSURE],
                "approach": "collaborative"
            }
        }
    
    async def analyze_seller(self, conversation_history: List[Dict], seller_messages: List[str]) -> SellerAnalysis:
        """Analyze seller personality and characteristics"""
        
        # Combine all seller messages for analysis
        all_seller_text = " ".join(seller_messages).lower()
        
        # Determine personality type
        personality_scores = {}
        for personality, patterns in self.personality_patterns.items():
            score = 0
            for keyword in patterns["keywords"]:
                score += all_seller_text.count(keyword)
            personality_scores[personality] = score
        
        # Get dominant personality
        dominant_personality = max(personality_scores.items(), key=lambda x: x[1])[0]
        
        # Calculate flexibility score
        flexibility_indicators = [
            "negotiable", "flexible", "open", "consider", "discuss", "maybe", "possibly"
        ]
        flexibility_score = sum(all_seller_text.count(word) for word in flexibility_indicators) / len(seller_messages) if seller_messages else 0
        flexibility_score = min(flexibility_score / 3, 1.0)  # Normalize to 0-1
        
        # Calculate urgency level
        urgency_indicators = [
            "quick", "fast", "urgent", "soon", "immediately", "asap", "need to sell"
        ]
        urgency_score = sum(all_seller_text.count(word) for word in urgency_indicators) / len(seller_messages) if seller_messages else 0
        urgency_score = min(urgency_score / 2, 1.0)  # Normalize to 0-1
        
        # Analyze response patterns
        response_patterns = {
            "average_response_length": sum(len(msg.split()) for msg in seller_messages) / len(seller_messages) if seller_messages else 0,
            "question_frequency": sum(msg.count("?") for msg in seller_messages) / len(seller_messages) if seller_messages else 0,
            "exclamation_frequency": sum(msg.count("!") for msg in seller_messages) / len(seller_messages) if seller_messages else 0
        }
        
        # Extract motivations
        motivations = self._extract_motivations(all_seller_text)
        
        # Extract constraints
        constraints = self._extract_constraints(all_seller_text)
        
        return SellerAnalysis(
            personality_type=dominant_personality,
            flexibility_score=flexibility_score,
            urgency_level=urgency_score,
            price_sensitivity=0.5,  # Would be refined with more analysis
            communication_style=self.personality_patterns[dominant_personality]["response_style"],
            response_patterns=response_patterns,
            negotiation_history=conversation_history,
            motivations=motivations,
            constraints=constraints
        )
    
    def _extract_motivations(self, text: str) -> List[str]:
        """Extract seller motivations from text"""
        motivations = []
        
        motivation_patterns = {
            "need_money": ["need money", "cash", "bills", "expenses", "broke"],
            "moving": ["moving", "relocate", "new house", "apartment"],
            "upgrade": ["upgrade", "new one", "better", "newer"],
            "space": ["space", "room", "storage", "declutter"],
            "unused": ["don't use", "rarely use", "collecting dust"]
        }
        
        for motivation, keywords in motivation_patterns.items():
            if any(keyword in text for keyword in keywords):
                motivations.append(motivation)
        
        return motivations
    
    def _extract_constraints(self, text: str) -> List[str]:
        """Extract seller constraints from text"""
        constraints = []
        
        constraint_patterns = {
            "time_pressure": ["soon", "quick", "urgent", "deadline"],
            "minimum_price": ["won't go below", "minimum", "lowest", "can't take less"],
            "condition_concerns": ["condition", "as-is", "no warranty", "final sale"],
            "location_constraints": ["pickup only", "no delivery", "local only"]
        }
        
        for constraint, keywords in constraint_patterns.items():
            if any(keyword in text for keyword in keywords):
                constraints.append(constraint)
        
        return constraints
    
    async def generate_market_intelligence(self, product_info: Dict) -> MarketIntelligence:
        """Generate market intelligence for the product"""
        
        # Mock market analysis - in production, this would call real APIs
        base_price = product_info.get("listed_price", 100)
        
        # Generate comparable prices (±20% of base price)
        comparable_prices = [
            base_price * random.uniform(0.8, 1.2) for _ in range(10)
        ]
        
        average_market_price = sum(comparable_prices) / len(comparable_prices)
        
        # Determine price trend
        trend_factor = random.uniform(-0.1, 0.1)
        price_trend = "rising" if trend_factor > 0.05 else "falling" if trend_factor < -0.05 else "stable"
        
        # Market saturation (0-1, higher means more competition)
        market_saturation = random.uniform(0.3, 0.8)
        
        return MarketIntelligence(
            comparable_prices=comparable_prices,
            average_market_price=average_market_price,
            price_trend=price_trend,
            market_saturation=market_saturation,
            seasonal_factors={"season": "neutral", "holiday_effect": 0.1},
            demand_indicators={"search_volume": 0.7, "listing_frequency": 0.6},
            supply_indicators={"inventory_level": 0.5, "new_listings": 0.4}
        )
    
    async def recommend_tactics(
        self,
        seller_analysis: SellerAnalysis,
        market_intelligence: MarketIntelligence,
        negotiation_context: Dict,
        current_phase: NegotiationPhase
    ) -> List[Tuple[NegotiationTactic, float, str]]:
        """Recommend the best tactics with confidence scores and rationale"""
        
        recommendations = []
        
        # Get personality-based tactics
        personality_info = self.personality_patterns[seller_analysis.personality_type]
        effective_tactics = personality_info["effective_tactics"]
        
        for tactic in effective_tactics:
            if tactic in self.tactic_effectiveness:
                effectiveness = self.tactic_effectiveness[tactic]
                
                # Calculate context-adjusted confidence
                confidence = self._calculate_tactic_confidence(
                    effectiveness, seller_analysis, market_intelligence, negotiation_context, current_phase
                )
                
                # Generate rationale
                rationale = self._generate_tactic_rationale(
                    tactic, seller_analysis, market_intelligence, current_phase
                )
                
                recommendations.append((tactic, confidence, rationale))
        
        # Add phase-specific tactics
        phase_tactics = self._get_phase_specific_tactics(current_phase, seller_analysis)
        for tactic, base_confidence, rationale in phase_tactics:
            if not any(rec[0] == tactic for rec in recommendations):
                recommendations.append((tactic, base_confidence, rationale))
        
        # Sort by confidence score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _calculate_tactic_confidence(
        self,
        effectiveness: TacticEffectiveness,
        seller_analysis: SellerAnalysis,
        market_intelligence: MarketIntelligence,
        context: Dict,
        phase: NegotiationPhase
    ) -> float:
        """Calculate confidence score for a tactic"""
        
        base_confidence = effectiveness.success_rate
        
        # Adjust for seller flexibility
        flexibility_bonus = seller_analysis.flexibility_score * 0.2
        
        # Adjust for market conditions
        market_bonus = 0
        if market_intelligence.average_market_price < context.get("target_price", 0):
            market_bonus = 0.1
        
        # Adjust for negotiation phase
        phase_modifier = self._get_phase_modifier(phase, effectiveness.tactic)
        
        # Adjust for seller personality match
        personality_bonus = 0.1 if effectiveness.tactic in self.personality_patterns[seller_analysis.personality_type]["effective_tactics"] else -0.1
        
        final_confidence = base_confidence + flexibility_bonus + market_bonus + phase_modifier + personality_bonus
        
        return max(0, min(1.0, final_confidence))
    
    def _get_phase_modifier(self, phase: NegotiationPhase, tactic: NegotiationTactic) -> float:
        """Get phase-specific modifier for tactic effectiveness"""
        
        phase_tactic_modifiers = {
            NegotiationPhase.GREETING: {
                NegotiationTactic.LIKING: 0.2,
                NegotiationTactic.INFORMATION_GATHERING: 0.3
            },
            NegotiationPhase.DISCOVERY: {
                NegotiationTactic.INFORMATION_GATHERING: 0.3,
                NegotiationTactic.VALUE_STACKING: 0.2
            },
            NegotiationPhase.ACTIVE_NEGOTIATION: {
                NegotiationTactic.ANCHORING: 0.2,
                NegotiationTactic.RECIPROCITY: 0.1
            },
            NegotiationPhase.CLOSING: {
                NegotiationTactic.COMPROMISE: 0.3,
                NegotiationTactic.DEADLINE_PRESSURE: 0.2
            }
        }
        
        return phase_tactic_modifiers.get(phase, {}).get(tactic, 0)
    
    def _get_phase_specific_tactics(
        self,
        phase: NegotiationPhase,
        seller_analysis: SellerAnalysis
    ) -> List[Tuple[NegotiationTactic, float, str]]:
        """Get tactics specifically suited for the current phase"""
        
        phase_tactics = {
            NegotiationPhase.GREETING: [
                (NegotiationTactic.LIKING, 0.8, "Build rapport and establish connection"),
                (NegotiationTactic.INFORMATION_GATHERING, 0.9, "Gather key information about seller's situation")
            ],
            NegotiationPhase.DISCOVERY: [
                (NegotiationTactic.VALUE_STACKING, 0.7, "Understand total value proposition"),
                (NegotiationTactic.INFORMATION_GATHERING, 0.8, "Learn seller's motivations and constraints")
            ],
            NegotiationPhase.INITIAL_POSITIONING: [
                (NegotiationTactic.ANCHORING, 0.9, "Set favorable reference point for negotiation"),
                (NegotiationTactic.FRAMING, 0.7, "Present offer in most favorable light")
            ],
            NegotiationPhase.ACTIVE_NEGOTIATION: [
                (NegotiationTactic.RECIPROCITY, 0.8, "Use give-and-take to build momentum"),
                (NegotiationTactic.CONTRAST_PRINCIPLE, 0.6, "Make offer seem reasonable by comparison")
            ],
            NegotiationPhase.CLOSING: [
                (NegotiationTactic.COMPROMISE, 0.9, "Find mutually acceptable solution"),
                (NegotiationTactic.INCREMENTAL_COMMITMENT, 0.7, "Secure agreement on key points")
            ]
        }
        
        return phase_tactics.get(phase, [])
    
    def _generate_tactic_rationale(
        self,
        tactic: NegotiationTactic,
        seller_analysis: SellerAnalysis,
        market_intelligence: MarketIntelligence,
        phase: NegotiationPhase
    ) -> str:
        """Generate human-readable rationale for tactic recommendation"""
        
        rationales = {
            NegotiationTactic.ANCHORING: f"Strong anchoring opportunity - seller shows {seller_analysis.flexibility_score:.1%} flexibility",
            NegotiationTactic.SCARCITY: f"Create urgency - market has {market_intelligence.market_saturation:.1%} saturation",
            NegotiationTactic.VALUE_STACKING: f"Emphasize value - seller is {seller_analysis.personality_type.value} type",
            NegotiationTactic.RECIPROCITY: f"Build goodwill - seller shows cooperative tendencies",
            NegotiationTactic.COMPROMISE: f"Seek middle ground - both parties have shown flexibility",
            NegotiationTactic.INFORMATION_GATHERING: f"Learn more - {len(seller_analysis.motivations)} motivations identified"
        }
        
        return rationales.get(tactic, f"Effective for {phase.value} phase with {seller_analysis.personality_type.value} sellers")
    
    async def generate_strategic_response(
        self,
        tactic: NegotiationTactic,
        context: Dict,
        seller_message: str,
        seller_analysis: SellerAnalysis,
        market_intelligence: MarketIntelligence
    ) -> str:
        """Generate a strategic response using the specified tactic"""
        
        # Response templates by tactic
        response_generators = {
            NegotiationTactic.ANCHORING: self._generate_anchoring_response,
            NegotiationTactic.VALUE_STACKING: self._generate_value_stacking_response,
            NegotiationTactic.RECIPROCITY: self._generate_reciprocity_response,
            NegotiationTactic.SCARCITY: self._generate_scarcity_response,
            NegotiationTactic.COMPROMISE: self._generate_compromise_response,
            NegotiationTactic.INFORMATION_GATHERING: self._generate_information_gathering_response
        }
        
        generator = response_generators.get(tactic)
        if generator:
            return await generator(context, seller_message, seller_analysis, market_intelligence)
        else:
            return await self._generate_generic_response(context, seller_message, seller_analysis)
    
    async def _generate_anchoring_response(
        self, context: Dict, seller_message: str, seller_analysis: SellerAnalysis, market_intel: MarketIntelligence
    ) -> str:
        """Generate anchoring tactic response"""
        
        target_price = context.get("target_price", 0)
        listed_price = context.get("listed_price", 0)
        
        # Start with lower anchor
        anchor_price = target_price * 0.85
        market_reference = market_intel.average_market_price
        
        responses = [
            f"I've been researching similar items and found comparable ones selling for around ${market_reference:.0f}. Would you consider ${anchor_price:.0f}?",
            f"Based on current market prices, I was thinking more in the range of ${anchor_price:.0f}. What are your thoughts?",
            f"I've seen similar items priced at ${market_reference:.0f}. Could we start our discussion around ${anchor_price:.0f}?"
        ]
        
        return random.choice(responses)
    
    async def _generate_value_stacking_response(
        self, context: Dict, seller_message: str, seller_analysis: SellerAnalysis, market_intel: MarketIntelligence
    ) -> str:
        """Generate value stacking response"""
        
        responses = [
            "I appreciate the quality of this item. Considering the condition and included accessories, what would be your best price?",
            "This looks like a great product with good value. I'm interested in the complete package - what's your most competitive price?",
            "I can see this is well-maintained and comes with everything. What's the best deal you can offer for the complete set?"
        ]
        
        return random.choice(responses)
    
    async def _generate_reciprocity_response(
        self, context: Dict, seller_message: str, seller_analysis: SellerAnalysis, market_intel: MarketIntelligence
    ) -> str:
        """Generate reciprocity-based response"""
        
        responses = [
            "I appreciate you being flexible on the price. In return, I can pick it up at your convenience and pay cash.",
            "Since you're working with me on the price, I'm happy to meet you halfway on the pickup time and location.",
            "I value your willingness to negotiate. How about if I can pick it up today - could you do a bit better on the price?"
        ]
        
        return random.choice(responses)
    
    async def _generate_scarcity_response(
        self, context: Dict, seller_message: str, seller_analysis: SellerAnalysis, market_intel: MarketIntelligence
    ) -> str:
        """Generate scarcity-based response"""
        
        responses = [
            "I'm very interested and ready to make a decision today. Could you work with me on the price?",
            "I've been looking for exactly this item and I'm prepared to buy it now. What's your best offer?",
            "I need to make a decision by this weekend. If you can meet my budget, I'll take it right away."
        ]
        
        return random.choice(responses)
    
    async def _generate_compromise_response(
        self, context: Dict, seller_message: str, seller_analysis: SellerAnalysis, market_intel: MarketIntelligence
    ) -> str:
        """Generate compromise response"""
        
        target_price = context.get("target_price", 0)
        listed_price = context.get("listed_price", 0)
        middle_price = (target_price + listed_price) / 2
        
        responses = [
            f"I understand your position. How about we meet in the middle at ${middle_price:.0f}?",
            f"Let's find a number that works for both of us. Would ${middle_price:.0f} be reasonable?",
            f"I'm willing to compromise. What do you think about ${middle_price:.0f}?"
        ]
        
        return random.choice(responses)
    
    async def _generate_information_gathering_response(
        self, context: Dict, seller_message: str, seller_analysis: SellerAnalysis, market_intel: MarketIntelligence
    ) -> str:
        """Generate information gathering response"""
        
        responses = [
            "This looks great! Can you tell me more about why you're selling it?",
            "I'm interested! How long have you had it, and are you looking to sell quickly?",
            "Nice item! What made you decide to sell, and is the price negotiable?",
            "I like what I see. Is there any flexibility on the price, and when do you need it sold by?"
        ]
        
        return random.choice(responses)
    
    async def _generate_generic_response(
        self, context: Dict, seller_message: str, seller_analysis: SellerAnalysis
    ) -> str:
        """Generate generic professional response"""
        
        responses = [
            "Thank you for the information. I'm very interested in moving forward.",
            "I appreciate your response. Let me know how we can work something out.",
            "That sounds reasonable. I'm ready to discuss the details further.",
            "I understand. I'm definitely interested and hope we can reach an agreement."
        ]
        
        return random.choice(responses)
    
    def calculate_negotiation_score(
        self,
        initial_price: float,
        current_offer: float,
        target_price: float,
        max_budget: float
    ) -> Dict[str, Any]:
        """Calculate comprehensive negotiation performance score"""
        
        if initial_price == 0 or current_offer == 0:
            return {"error": "Invalid prices"}
        
        # Calculate savings
        absolute_savings = initial_price - current_offer
        percentage_savings = (absolute_savings / initial_price) * 100
        
        # Calculate target achievement
        target_distance = abs(current_offer - target_price)
        target_achievement = max(0, 100 - (target_distance / target_price * 100))
        
        # Calculate budget efficiency
        budget_usage = (current_offer / max_budget) * 100
        budget_efficiency = max(0, 100 - budget_usage)
        
        # Overall score (weighted average)
        overall_score = (
            percentage_savings * 0.4 +
            target_achievement * 0.4 +
            budget_efficiency * 0.2
        )
        
        return {
            "overall_score": round(overall_score, 1),
            "absolute_savings": round(absolute_savings, 2),
            "percentage_savings": round(percentage_savings, 1),
            "target_achievement": round(target_achievement, 1),
            "budget_efficiency": round(budget_efficiency, 1),
            "performance_grade": self._get_performance_grade(overall_score)
        }
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

# Example usage and testing
async def demo_negotiation_intelligence():
    """Demo the negotiation intelligence system"""
    print("🧠 AI Negotiation Intelligence Demo")
    print("=" * 50)
    
    # Initialize intelligence engine
    intel_engine = NegotiationIntelligenceEngine()
    
    # Mock seller conversation
    seller_messages = [
        "Hi! Thanks for your interest in my iPhone. It's in excellent condition.",
        "I'm asking $800 for it, but I might consider $780 if you can pick it up soon.",
        "I need to sell it quickly because I'm moving next week."
    ]
    
    # Analyze seller
    print("📊 Analyzing seller...")
    seller_analysis = await intel_engine.analyze_seller([], seller_messages)
    
    print(f"Seller Personality: {seller_analysis.personality_type.value}")
    print(f"Flexibility Score: {seller_analysis.flexibility_score:.2f}")
    print(f"Urgency Level: {seller_analysis.urgency_level:.2f}")
    print(f"Motivations: {', '.join(seller_analysis.motivations)}")
    
    # Generate market intelligence
    print("\n📈 Generating market intelligence...")
    product_info = {"listed_price": 800, "name": "iPhone 13 Pro"}
    market_intel = await intel_engine.generate_market_intelligence(product_info)
    
    print(f"Average Market Price: ${market_intel.average_market_price:.0f}")
    print(f"Price Trend: {market_intel.price_trend}")
    print(f"Market Saturation: {market_intel.market_saturation:.1%}")
    
    # Recommend tactics
    print("\n🎯 Recommending tactics...")
    context = {"target_price": 650, "listed_price": 800}
    current_phase = NegotiationPhase.ACTIVE_NEGOTIATION
    
    tactic_recommendations = await intel_engine.recommend_tactics(
        seller_analysis, market_intel, context, current_phase
    )
    
    for i, (tactic, confidence, rationale) in enumerate(tactic_recommendations, 1):
        print(f"{i}. {tactic.value.title().replace('_', ' ')} (Confidence: {confidence:.1%})")
        print(f"   Rationale: {rationale}")
    
    # Generate strategic response
    print("\n💬 Generating strategic response...")
    top_tactic = tactic_recommendations[0][0]
    response = await intel_engine.generate_strategic_response(
        top_tactic, context, seller_messages[-1], seller_analysis, market_intel
    )
    
    print(f"Using {top_tactic.value.replace('_', ' ').title()} tactic:")
    print(f"Response: {response}")
    
    # Calculate negotiation score
    print("\n📊 Negotiation Performance:")
    score_data = intel_engine.calculate_negotiation_score(800, 720, 650, 750)
    
    print(f"Overall Score: {score_data['overall_score']}/100 (Grade: {score_data['performance_grade']})")
    print(f"Savings: ${score_data['absolute_savings']} ({score_data['percentage_savings']}%)")
    print(f"Target Achievement: {score_data['target_achievement']}%")
    
    print("\n✅ Intelligence demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_negotiation_intelligence())