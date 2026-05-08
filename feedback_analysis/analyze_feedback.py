#!/usr/bin/env python3
"""
Phasma AI Feedback Analysis Tool
Analyzes and consolidates feedback from multiple AI systems
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict, Counter

class FeedbackAnalyzer:
    def __init__(self, feedback_dir: str = "feedback_analysis"):
        self.feedback_dir = feedback_dir
        self.ai_files = {
            'AI1': 'AI1_feedback.txt',
            'AI2': 'AI2_feedback.txt',
            'AI3': 'AI3_feedback.txt',
            'AI4': 'AI4_feedback.txt'
        }

    def load_feedback(self, ai_name: str) -> str:
        """Load feedback from a specific AI file"""
        file_path = os.path.join(self.feedback_dir, self.ai_files[ai_name])
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Remove the template header and just get the actual feedback
                if '[PASTE' in content:
                    return content.split('[PASTE')[1].split(']')[0].strip()
                return content
        except FileNotFoundError:
            return ""
        except Exception as e:
            print(f"Error loading {ai_name} feedback: {e}")
            return ""

    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases and technical terms from feedback"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        # Extract technical terms and key phrases
        key_phrases = []

        # Technical patterns
        technical_patterns = [
            r'Monte Carlo', r'Brownian motion', r'volatility', r'drift',
            r'confidence', r'win rate', r'position sizing', r'risk management',
            r'options trading', r'technical analysis', r'pattern detection',
            r'reality check', r'historical analogs', r'news integration',
            r'API integration', r'performance', r'optimization', r'cache',
            r'simulation', r'backtesting', r'validation', r'error handling'
        ]

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Meaningful sentences only
                # Check for technical terms
                for pattern in technical_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        key_phrases.append(sentence)
                        break

                # Also capture improvement suggestions
                if any(word in sentence.lower() for word in ['improve', 'enhance', 'optimize', 'fix', 'add', 'implement', 'should', 'could', 'would', 'need']):
                    key_phrases.append(sentence)

        return key_phrases

    def categorize_feedback(self, text: str) -> Dict[str, List[str]]:
        """Categorize feedback into different areas"""
        categories = {
            'architecture': [],
            'performance': [],
            'accuracy': [],
            'usability': [],
            'risk_management': [],
            'technical': [],
            'integration': [],
            'documentation': []
        }

        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            sentence = sentence.strip().lower()

            # Categorize based on keywords
            if any(word in sentence for word in ['architecture', 'design', 'structure', 'component', 'module', 'system']):
                categories['architecture'].append(sentence)
            elif any(word in sentence for word in ['performance', 'speed', 'efficiency', 'optimization', 'cache', 'memory']):
                categories['performance'].append(sentence)
            elif any(word in sentence for word in ['accuracy', 'precision', 'validation', 'error', 'bug', 'fix']):
                categories['accuracy'].append(sentence)
            elif any(word in sentence for word in ['user', 'interface', 'experience', 'ui', 'display', 'output']):
                categories['usability'].append(sentence)
            elif any(word in sentence for word in ['risk', 'position', 'capital', 'money', 'loss', 'profit']):
                categories['risk_management'].append(sentence)
            elif any(word in sentence for word in ['technical', 'code', 'implementation', 'algorithm', 'method']):
                categories['technical'].append(sentence)
            elif any(word in sentence for word in ['integration', 'api', 'connection', 'interface', 'external']):
                categories['integration'].append(sentence)
            elif any(word in sentence for word in ['documentation', 'readme', 'comment', 'explain']):
                categories['documentation'].append(sentence)

        return categories

    def find_similarities(self, feedback1: Dict, feedback2: Dict, feedback3: Dict, feedback4: Dict) -> Dict[str, List]:
        """Find similarities across all four AI feedback"""
        similarities = defaultdict(list)

        # Get all unique keys from categorizations
        all_keys = set(feedback1.keys()) | set(feedback2.keys()) | set(feedback3.keys()) | set(feedback4.keys())

        for category in all_keys:
            sentences1 = feedback1.get(category, [])
            sentences2 = feedback2.get(category, [])
            sentences3 = feedback3.get(category, [])
            sentences4 = feedback4.get(category, [])

            # Find common themes
            all_sentences = sentences1 + sentences2 + sentences3 + sentences4
            if len(all_sentences) > len(set(sentences1 + sentences2 + sentences3 + sentences4)) // 2:
                similarities[category].extend(all_sentences)

        return similarities

    def generate_improvement_roadmap(self, consolidated_feedback: Dict) -> List[Dict]:
        """Generate prioritized improvement roadmap"""
        improvements = []

        # Priority 1: Critical issues (accuracy, risk management)
        critical = consolidated_feedback.get('accuracy', []) + consolidated_feedback.get('risk_management', [])
        for item in critical[:5]:  # Top 5 critical
            improvements.append({
                'priority': 'CRITICAL',
                'category': 'accuracy_risk',
                'description': item,
                'effort': 'Medium',
                'impact': 'High'
            })

        # Priority 2: Performance improvements
        performance = consolidated_feedback.get('performance', [])
        for item in performance[:3]:
            improvements.append({
                'priority': 'HIGH',
                'category': 'performance',
                'description': item,
                'effort': 'Low',
                'impact': 'Medium'
            })

        # Priority 3: Technical enhancements
        technical = consolidated_feedback.get('technical', [])
        for item in technical[:3]:
            improvements.append({
                'priority': 'MEDIUM',
                'category': 'technical',
                'description': item,
                'effort': 'High',
                'impact': 'Medium'
            })

        return improvements

    def analyze_all_feedback(self) -> Dict:
        """Complete analysis of all AI feedback"""
        print("🔍 Analyzing feedback from all AI systems...")

        # Load all feedback
        ai1_text = self.load_feedback('AI1')
        ai2_text = self.load_feedback('AI2')
        ai3_text = self.load_feedback('AI3')
        ai4_text = self.load_feedback('AI4')

        print(f"📊 Feedback lengths: AI1={len(ai1_text)} chars, AI2={len(ai2_text)} chars, AI3={len(ai3_text)} chars, AI4={len(ai4_text)} chars")

        # Extract key phrases
        ai1_phrases = self.extract_key_phrases(ai1_text)
        ai2_phrases = self.extract_key_phrases(ai2_text)
        ai3_phrases = self.extract_key_phrases(ai3_text)
        ai4_phrases = self.extract_key_phrases(ai4_text)

        # Categorize feedback
        ai1_categories = self.categorize_feedback(ai1_text)
        ai2_categories = self.categorize_feedback(ai2_text)
        ai3_categories = self.categorize_feedback(ai3_text)
        ai4_categories = self.categorize_feedback(ai4_text)

        # Find similarities
        similarities = self.find_similarities(ai1_categories, ai2_categories, ai3_categories, ai4_categories)

        # Generate improvement roadmap
        roadmap = self.generate_improvement_roadmap(similarities)

        return {
            'ai1_key_phrases': ai1_phrases,
            'ai2_key_phrases': ai2_phrases,
            'ai3_key_phrases': ai3_phrases,
            'ai4_key_phrases': ai4_phrases,
            'categorizations': {
                'AI1': ai1_categories,
                'AI2': ai2_categories,
                'AI3': ai3_categories,
                'AI4': ai4_categories
            },
            'similarities': similarities,
            'improvement_roadmap': roadmap,
            'timestamp': datetime.now().isoformat()
        }

    def update_consolidated_report(self, analysis: Dict):
        """Update the consolidated feedback report"""
        report_path = os.path.join(self.feedback_dir, 'consolidated_feedback.md')

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Phasma AI Feedback Analysis - Consolidated Report\n\n")
            f.write(f"## 📊 Analysis Generated: {analysis['timestamp']}\n\n")

            # Individual AI summaries
            f.write("## 🎯 Individual AI Feedback Summaries\n\n")

            for ai_name in ['AI1', 'AI2', 'AI3']:
                categories = analysis['categorizations'][ai_name]
                f.write(f"### {ai_name} Analysis\n")
                for category, sentences in categories.items():
                    if sentences:
                        f.write(f"- **{category.upper()}**: {len(sentences)} items\n")
                f.write(f"- **Key Phrases**: {len(analysis[f'{ai_name.lower()}_key_phrases'])} extracted\n\n")

            # Consolidated findings
            f.write("## 🔄 Consolidated Findings\n\n")
            f.write("### Common Themes (Identical/Similar Feedback Combined)\n\n")

            for category, items in analysis['similarities'].items():
                if items:
                    f.write(f"#### {category.upper()}\n")
                    f.write(f"- **Consensus**: {len(items)} related items found across AIs\n")
                    f.write(f"- **Priority**: {'HIGH' if len(items) >= 2 else 'MEDIUM'}\n\n")

            # Implementation roadmap
            f.write("## 🚀 Implementation Roadmap\n\n")

            priority_groups = defaultdict(list)
            for item in analysis['improvement_roadmap']:
                priority_groups[item['priority']].append(item)

            for priority in ['CRITICAL', 'HIGH', 'MEDIUM']:
                if priority_groups[priority]:
                    f.write(f"### {priority} Priority ({len(priority_groups[priority])} items)\n\n")
                    for i, item in enumerate(priority_groups[priority], 1):
                        f.write(f"{i}. **{item['category'].upper()}**\n")
                        f.write(f"   - Description: {item['description']}\n")
                        f.write(f"   - Effort: {item['effort']} | Impact: {item['impact']}\n\n")

def main():
    """Main analysis function"""
    analyzer = FeedbackAnalyzer()
    analysis = analyzer.analyze_all_feedback()

    print("✅ Analysis complete!")
    print(f"📊 Found {len(analysis['similarities'])} categories with common themes")
    print(f"🚀 Generated {len(analysis['improvement_roadmap'])} improvement recommendations")

    # Update consolidated report
    analyzer.update_consolidated_report(analysis)
    print("📝 Consolidated report updated")

if __name__ == "__main__":
    main()
