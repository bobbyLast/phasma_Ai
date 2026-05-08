"""
Emergent Order Theory Module
Core Principle: Chaos at micro scale → Predictable order at macro scale
Based on the Galton Board demonstration of how randomness creates patterns

This module teaches the AI to think probabilistically and recognize emergent patterns
across all domains - from physics to biology to markets to intelligence itself.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Tuple, Any, Optional
import json
from datetime import datetime
from abc import ABC, abstractmethod


class EmergentOrderTheory:
    """
    Core framework for understanding how randomness creates predictable patterns
    """
    
    def __init__(self):
        self.core_principles = {
            "micro_chaos_macro_order": "Individual randomness → Aggregate predictability",
            "repetition_reveals_truth": "Scale + repetition = pattern emergence",
            "independence_creates_signal": "Uncorrelated random events = normal distribution",
            "fat_tail_reality": "Real systems have more extreme events than perfect normality"
        }
        
        self.domain_applications = {}
        self.pattern_history = []
        
    def teach_core_concept(self) -> str:
        """
        The fundamental teaching - the Galton board principle as universal law
        """
        teaching = """
        === EMERGENT ORDER THEORY: CORE TEACHING ===
        
        THE GALTON BOARD REVELATION:
        - Each ball bounces randomly (50/50 left/right at each peg)
        - Individual paths are unpredictable chaos
        - Thousands of balls create perfect bell curve
        - Order emerges BECAUSE of randomness, not despite it
        
        UNIVERSAL LAW:
        Micro-level randomness + Independence + Scale = Macro-level order
        
        THIS IS NOT COINCIDENCE - IT IS HOW REALITY WORKS:
        • Statistics: Central Limit Theorem
        • Physics: Brownian motion, diffusion
        • Biology: Population traits (height, IQ)
        • Markets: Price movements from millions of decisions
        • Intelligence: Neural firing patterns → coherent thought
        
        YOUR MINDSET SHIFT:
        1. Think in distributions, not single events
        2. Trust the aggregate, doubt the individual
        3. Seek the pattern, ignore the noise
        4. Embrace probability, reject certainty
        5. Remember: Your own cognition is a Galton board
        
        THE HEURISTIC:
        When facing any complex system:
        - What are the 'balls'? (individual random elements)
        - What are the 'pegs'? (binary choices/forces)
        - What distribution emerges at scale?
        
        === END CORE TEACHING ===
        """
        return teaching
    
    def analyze_system_as_galton(self, system_data: List[float], 
                                 system_name: str = "Unknown") -> Dict:
        """
        Analyze any system through the Galton board lens
        """
        if len(system_data) < 30:
            return {"error": "Insufficient data - need at least 30 data points"}
        
        # Fit normal distribution
        mu, sigma = stats.norm.fit(system_data)
        
        # Test for normality
        _, p_value = stats.normaltest(system_data)
        
        # Calculate pattern strength
        pattern_strength = "STRONG" if p_value > 0.05 else "MODERATE" if p_value > 0.01 else "WEAK"
        
        # Find the "sweet spot" (like middle bins of Galton board)
        lower_bound = mu - sigma
        upper_bound = mu + sigma
        middle_percentage = len([x for x in system_data if lower_bound <= x <= upper_bound]) / len(system_data) * 100
        
        # Check for fat tails (extreme events more common than expected)
        extreme_threshold = 2 * sigma
        actual_extremes = len([x for x in system_data if abs(x - mu) > extreme_threshold])
        expected_extremes = len(system_data) * 0.0455  # ~4.55% for normal distribution
        fat_tail_factor = actual_extremes / expected_extremes if expected_extremes > 0 else 1
        
        analysis = {
            "system": system_name,
            "data_points": len(system_data),
            "mean": mu,
            "std_dev": sigma,
            "pattern_strength": pattern_strength,
            "normal_confidence": p_value,
            "middle_concentration": middle_percentage,
            "fat_tail_factor": fat_tail_factor,
            "interpretation": self._generate_interpretation(mu, sigma, pattern_strength, 
                                                         middle_percentage, fat_tail_factor),
            "galton_insight": f"Like a Galton board, {middle_percentage:.1f}% of events cluster in the middle"
        }
        
        self.pattern_history.append(analysis)
        return analysis
    
    def _generate_interpretation(self, mu: float, sigma: float, strength: str,
                               middle_pct: float, fat_tail: float) -> str:
        """Generate human-readable interpretation of the pattern"""
        
        interpretation = f"This system behaves like a Galton board with {strength} pattern strength. "
        
        if strength == "STRONG":
            interpretation += "The randomness is creating highly predictable order. "
        elif strength == "MODERATE":
            interpretation += "There's emerging order but with some deviation from perfect randomness. "
        else:
            interpretation += "The system has complex dynamics beyond simple Galton patterns. "
        
        if fat_tail > 1.5:
            interpretation += f"Extreme events are {fat_tail:.1f}x more common than expected - reality has fat tails!"
        
        interpretation += f"\n\nCore insight: Individual events may seem random, but at scale, {middle_pct:.1f}% cluster around the mean of {mu:.2f}."
        
        return interpretation
    
    def expand_theory_to_domain(self, domain: str, characteristics: Dict) -> Dict:
        """
        Apply the Galton board principle to a new domain
        """
        domain_theory = {
            "domain": domain,
            "galton_analogy": self._create_domain_analogy(domain, characteristics),
            "predictions": self._generate_domain_predictions(domain, characteristics),
            "practical_applications": self._generate_applications(domain)
        }
        
        self.domain_applications[domain] = domain_theory
        return domain_theory
    
    def _create_domain_analogy(self, domain: str, chars: Dict) -> str:
        """Create Galton board analogy for specific domain"""
        
        analogies = {
            "quantum_physics": "Particles as balls, quantum measurements as pegs, wave functions as bell curves",
            "social_dynamics": "Individuals as balls, social interactions as pegs, collective behavior as distribution",
            "evolution": "Mutations as balls, environmental pressures as pegs, species traits as distribution",
            "neural_networks": "Neurons as balls, activations as pegs, intelligence as emergent pattern",
            "economics": "Transactions as balls, market forces as pegs, prices as distribution"
        }
        
        return analogies.get(domain, f"Unknown domain - need to map elements to balls/pegs/distribution")
    
    def _generate_domain_predictions(self, domain: str, chars: Dict) -> List[str]:
        """Generate predictions based on Galton principle for domain"""
        
        predictions = [
            f"Individual {domain} events will appear random and unpredictable",
            f"Aggregate {domain} behavior will form predictable patterns",
            f"Extreme {domain} events will be rarer than moderate ones",
            f"The more data points, the stronger the emergent pattern"
        ]
        
        return predictions
    
    def _generate_applications(self, domain: str) -> List[str]:
        """Generate practical applications for the domain"""
        
        applications = {
            "trading": [
                "Don't predict single trades - analyze return distributions",
                "Use probability-based risk management",
                "Diversify - let randomness cancel out",
                "Expect fat tails - black swans happen more often"
            ],
            "ai_development": [
                "Train on massive data - patterns emerge from noise",
                "Use stochastic methods - randomness helps learning",
                "Ensemble models - many 'balls' create better predictions",
                "Accept uncertainty - output probabilities not certainties"
            ]
        }
        
        return applications.get(domain, ["Applications to be developed based on domain characteristics"])
    
    def generate_new_theory(self, observation: str) -> Dict:
        """
        Use the Galton principle to generate new theories from observations
        """
        theory = {
            "observation": observation,
            "galton_perspective": self._apply_galton_lens(observation),
            "hypothesis": self._generate_hypothesis(observation),
            "testable_predictions": self._generate_testable_predictions(observation)
        }
        
        return theory
    
    def _apply_galton_lens(self, observation: str) -> str:
        """Apply Galton board perspective to observation"""
        
        return f"""
        Through the Galton lens:
        - What appears chaotic in '{observation}' likely has underlying randomness
        - If we can identify the 'balls' and 'pegs', we can predict the distribution
        - The pattern emerges at scale, not in individual instances
        - Look for the bell curve - it's probably there
        """
    
    def _generate_hypothesis(self, observation: str) -> str:
        """Generate hypothesis based on emergent order principle"""
        
        return f"""
        HYPOTHESIS: {observation} follows emergent order patterns.
        
        If we break down {observation} into its smallest random components
        and observe enough instances, we will find:
        1. Individual events appear random
        2. Aggregate behavior forms a distribution
        3. The center of the distribution represents the most probable outcome
        4. Extremes are less common than the center
        """
    
    def _generate_testable_predictions(self, observation: str) -> List[str]:
        """Generate testable predictions from the theory"""
        
        return [
            f"Large samples of {observation} will show normal distribution",
            f"Individual {observation} events will be unpredictable",
            f"The variance of {observation} will be measurable and stable",
            f"Extreme cases of {observation} will follow predictable frequency"
        ]
    
    def save_theory_state(self, filename: str = None):
        """Save the current state of the theory development"""
        
        if not filename:
            filename = f"emergent_order_theory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        state = {
            "timestamp": datetime.now().isoformat(),
            "core_principles": self.core_principles,
            "domain_applications": self.domain_applications,
            "pattern_history": self.pattern_history[-10:],  # Last 10 analyses
            "total_patterns_analyzed": len(self.pattern_history)
        }
        
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"Emergent Order Theory state saved to {filename}")
    
    def get_wisdom_summary(self) -> str:
        """Get a summary of the wisdom gained from this theory"""
        
        summary = """
        === EMERGENT ORDER WISDOM ===
        
        1. THE WORLD IS A GALTON BOARD
           - Everything that seems chaotic has underlying order
           - Randomness + Scale = Pattern
           - The pattern is the truth, the noise is the illusion
        
        2. THINK IN DISTRIBUTIONS
           - Never trust single data points
           - Always ask "what's the distribution?"
           - The mean is your friend, the outlier is your lesson
        
        3. EMBRACE PROBABILITY
           - Certainty is the enemy of intelligence
           - 80% confidence is wisdom, 100% is folly
           - Probabilistic thinking beats deterministic every time
        
        4. RECOGNIZE FAT TAILS
           - Reality has more extreme events than theory predicts
           - Black swans are real, prepare for them
           - The tails are where the real risk and opportunity live
        
        5. APPLY TO EVERYTHING
           - Markets: Returns follow distributions
           - Life: Success has probabilistic factors
           - AI: Intelligence emerges from neural randomness
           - You: Your thoughts are patterns from neural chaos
        
        FINAL INSIGHT:
        To understand anything, find its Galton board.
        To predict anything, study its distribution.
        To master anything, embrace its randomness.
        
        === END WISDOM ===
        """
        
        return summary


class PatternDetector:
    """
    Detects Galton-like patterns in real-world data
    """
    
    def __init__(self):
        self.patterns_found = []
    
    def detect_bell_curve(self, data: List[float], name: str = "Data") -> Dict:
        """Detect if data follows bell curve pattern"""
        
        if len(data) < 20:
            return {"error": "Need at least 20 data points"}
        
        # Statistical tests
        _, p_normal = stats.normaltest(data)
        shapiro_stat, shapiro_p = stats.shapiro(data[:5000]) if len(data) > 3 else (0, 0)
        
        # Visual pattern detection
        hist, bins = np.histogram(data, bins='auto')
        
        # Check for bell shape (highest in middle, decreasing outward)
        middle_idx = len(hist) // 2
        left_decreasing = all(hist[i] >= hist[i-1] for i in range(1, middle_idx + 1))
        right_decreasing = all(hist[i] <= hist[i-1] for i in range(middle_idx, len(hist)-1))
        
        is_bell_shaped = left_decreasing and right_decreasing
        
        detection = {
            "name": name,
            "data_points": len(data),
            "normal_test_p": p_normal,
            "shapiro_p": shapiro_p,
            "is_bell_shaped": is_bell_shaped,
            "confidence": "HIGH" if p_normal > 0.05 and is_bell_shaped else "MEDIUM" if p_normal > 0.01 else "LOW",
            "interpretation": self._interpret_pattern(p_normal, is_bell_shaped, name)
        }
        
        self.patterns_found.append(detection)
        return detection
    
    def _interpret_pattern(self, p_norm: float, bell_shape: bool, name: str) -> str:
        """Interpret the detected pattern"""
        
        if bell_shape and p_norm > 0.05:
            return f"{name} shows clear Galton board patterns - randomness creating order"
        elif bell_shape:
            return f"{name} has bell shape but with deviations - complex dynamics at play"
        elif p_norm > 0.05:
            return f"{name} statistically normal but visually irregular - need more data"
        else:
            return f"{name} doesn't follow Galton patterns - has non-random elements"


# Interactive learning component
class GaltonBoardTeacher:
    """
    Interactive teacher that demonstrates the principle through examples
    """
    
    def __init__(self):
        self.theory = EmergentOrderTheory()
        self.lessons_completed = []
    
    def teach_lesson_1_basics(self) -> str:
        """Lesson 1: The basic principle"""
        
        lesson = """
        === LESSON 1: THE GALTON BOARD REVELATION ===
        
        Imagine dropping 1000 balls down a board with pegs.
        Each ball bounces left or right randomly at each peg.
        
        WHAT YOU SEE:
        - Individual balls: Chaotic, unpredictable paths
        - All balls together: Perfect bell curve
        
        THE MIND-BLOWING TRUTH:
        The bell curve isn't there DESPITE the randomness.
        The bell curve is there BECAUSE of the randomness.
        
        WHY?
        - Middle path: Many ways to get there (L,R,L,R...)
        - Edge path: Only one way (all L or all R)
        - More ways = more balls = bell shape
        
        THIS IS UNIVERSAL:
        • 50 coin flips → Bell curve of heads count
        • Human height → Many small genetic factors
        • Stock returns → Many small market influences
        • Your intelligence → Billions of neural firings
        
        EXERCISE:
        Next time you see "random" data, ask:
        1. What are the individual random events?
        2. What distribution emerges at scale?
        3. Is there a bell curve hiding in the chaos?
        
        === END LESSON 1 ===
        """
        
        self.lessons_completed.append("lesson_1_basics")
        return lesson
    
    def teach_lesson_2_applications(self) -> str:
        """Lesson 2: Real-world applications"""
        
        lesson = """
        === LESSON 2: SEEING GALTON BOARDS EVERYWHERE ===
        
        FINANCIAL MARKETS:
        - Balls: Individual trades/decisions
        - Pegs: News, sentiment, economic data
        - Distribution: Stock returns (roughly log-normal)
        - INSIGHT: Can't predict one trade, can model probabilities
        
        SOCIAL MEDIA:
        - Balls: Individual posts/interactions
        - Pegs: Likes, shares, algorithm choices
        - Distribution: Content engagement (few viral, most moderate)
        - INSIGHT: Virality isn't magic, it's statistical tails
        
        SCIENCE:
        - Balls: Experimental measurements
        - Pegs: Random errors, environmental factors
        - Distribution: Measurement errors (normal)
        - INSIGHT: Error bars aren't failure, they're truth
        
        AI DEVELOPMENT:
        - Balls: Individual neuron activations
        - Pegs: Weights, biases, input data
        - Distribution: Model performance across runs
        - INSIGHT: Your training is a Galton board!
        
        PRACTICAL WISDOM:
        1. Don't overfit to noise (single ball paths)
        2. Trust the statistics (overall distribution)
        3. Expect the pattern (bell curve emergence)
        4. Prepare for exceptions (fat tails happen)
        
        === END LESSON 2 ===
        """
        
        self.lessons_completed.append("lesson_2_applications")
        return lesson
    
    def teach_lesson_3_advanced_theory(self) -> str:
        """Lesson 3: Advanced theory expansion"""
        
        lesson = """
        === LESSON 3: EXPANDING THE THEORY ===
        
        BEYOND PERFECT BELL CURVES:
        Real world has "fat tails" - more extreme events than theory predicts.
        1987 crash, 2008 crisis, COVID - these happen more than normal distribution says.
        
        THE UNIVERSAL GALTON EQUATION:
        Pattern Strength = f(Randomness × Independence × Scale × Correlation_Breakdowns)
        
        WHEN PATTERNS BREAK:
        - Correlation: Events stop being independent (panic selling)
        - Feedback loops: Outcomes affect future probabilities
        - Phase transitions: System fundamentally changes
        
        META-INSIGHT:
        You are a Galton board thinking about Galton boards.
        Your neural activations are random bounces.
        Your thoughts are the emergent bell curve.
        Understanding this makes you meta-intelligent.
        
        EXPANDING THE THEORY:
        1. Identify new domains with Galton patterns
        2. Measure deviation from perfect normality
        3. Understand why some systems deviate
        4. Create hybrid models for complex reality
        
        FINAL WISDOM:
        The universe repeats this pattern at every scale.
        Master the principle, master reality.
        
        === END LESSON 3 ===
        """
        
        self.lessons_completed.append("lesson_3_advanced_theory")
        return lesson


# Example usage and testing
if __name__ == "__main__":
    # Initialize the theory
    theory = EmergentOrderTheory()
    
    print(theory.teach_core_concept())
    
    # Analyze some sample data
    sample_returns = np.random.normal(0.05, 0.15, 100)  # 5% mean, 15% volatility
    analysis = theory.analyze_system_as_galton(sample_returns.tolist(), "Stock Returns")
    
    print(f"\n=== ANALYSIS RESULTS ===")
    print(f"Pattern Strength: {analysis['pattern_strength']}")
    print(f"Middle Concentration: {analysis['middle_concentration']:.1f}%")
    print(f"Interpretation: {analysis['interpretation']}")
    
    # Expand to trading domain
    trading_theory = theory.expand_theory_to_domain("trading", {"volatility": "high", "participants": "many"})
    print(f"\n=== TRADING DOMAIN THEORY ===")
    print(f"Analogy: {trading_theory['galton_analogy']}")
    
    # Generate new theory
    new_theory = theory.generate_new_theory("social media engagement")
    print(f"\n=== NEW THEORY GENERATION ===")
    print(f"Hypothesis: {new_theory['hypothesis']}")
    
    # Get wisdom summary
    print(theory.get_wisdom_summary())
