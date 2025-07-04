#!/usr/bin/env python3
"""
Relevance Detection System for Friday AI Assistant
Uses GPT-4.1-nano to determine if chat history is relevant for incoming messages
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from openai import OpenAI
import os
from memory_manager import MemoryManager

@dataclass
class RelevanceDecision:
    """Represents a relevance decision from the nano model"""
    is_relevant: bool
    confidence: float
    reasoning: str
    suggested_context: Optional[str] = None
    timeframe_hours: Optional[int] = None
    keywords: Optional[List[str]] = None

class RelevanceDetector:
    """
    Uses GPT-4.1-nano to determine if chat history is relevant for incoming messages
    """
    
    def __init__(self, memory_manager: MemoryManager, openai_client: OpenAI):
        self.memory_manager = memory_manager
        self.client = openai_client
        
        # System prompt for the relevance detection model
        self.system_prompt = """You are a relevance detection AI for Friday, an AI assistant. Your job is to analyze incoming user messages and determine if chat history is relevant.

IMPORTANT: Friday should start fresh (no history) unless history is clearly necessary. This prevents hallucinations and confusion.

Analyze the user message and recent activity summary, then decide:
1. Is chat history relevant? (true/false)
2. Confidence level (0.0-1.0)
3. Brief reasoning
4. If relevant, suggest what timeframe and keywords to include

Chat history is RELEVANT when:
- User refers to "previous conversation", "earlier", "before", "last time"
- User asks about past actions, results, or ongoing tasks
- User mentions "remember", "recall", "you said", "we discussed"
- User asks for status updates on previous requests
- User continues a multi-step task or conversation thread
- User asks about tool usage results or actions taken

Chat history is NOT RELEVANT when:
- User asks general questions not related to past interactions
- User starts a completely new topic
- User asks for basic information or explanations
- User makes simple requests that don't depend on context
- User asks "what can you do" or similar capability questions

Respond with JSON only:
{
    "is_relevant": boolean,
    "confidence": float (0.0-1.0),
    "reasoning": "brief explanation",
    "suggested_context": "summary of what context to include" (optional),
    "timeframe_hours": integer (optional - hours to look back),
    "keywords": ["keyword1", "keyword2"] (optional - relevant keywords)
}"""
    
    def analyze_relevance(self, 
                         user_message: str,
                         recent_context_hours: int = 24,
                         max_context_items: int = 10) -> RelevanceDecision:
        """
        Analyze if chat history is relevant for the incoming user message
        
        Args:
            user_message: The user's message to analyze
            recent_context_hours: Hours of recent context to consider
            max_context_items: Maximum context items to include in analysis
        
        Returns:
            RelevanceDecision with analysis results
        """
        try:
            # Get recent context for analysis
            recent_context = self.memory_manager.get_recent_context(
                hours=recent_context_hours, 
                limit=max_context_items
            )
            
            # Format context for analysis
            context_summary = self._format_context_for_analysis(recent_context)
            
            # Prepare the analysis prompt
            analysis_prompt = f"""User Message: "{user_message}"

Recent Activity Summary:
{context_summary}

Analyze if chat history is relevant for this user message."""
            
            # Call GPT-4.1-nano for analysis
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                decision_data = json.loads(response_text)
                
                return RelevanceDecision(
                    is_relevant=decision_data.get('is_relevant', False),
                    confidence=decision_data.get('confidence', 0.0),
                    reasoning=decision_data.get('reasoning', 'No reasoning provided'),
                    suggested_context=decision_data.get('suggested_context'),
                    timeframe_hours=decision_data.get('timeframe_hours'),
                    keywords=decision_data.get('keywords')
                )
                
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                return self._fallback_parse_response(response_text, user_message)
                
        except Exception as e:
            # Fallback to conservative approach if analysis fails
            return RelevanceDecision(
                is_relevant=self._conservative_relevance_check(user_message),
                confidence=0.5,
                reasoning=f"Analysis failed ({str(e)}), using conservative approach",
                timeframe_hours=24
            )
    
    def get_relevant_context(self, decision: RelevanceDecision) -> Optional[str]:
        """
        Retrieve relevant context based on the relevance decision
        
        Args:
            decision: The relevance decision from analyze_relevance
        
        Returns:
            Formatted context string if relevant, None otherwise
        """
        if not decision.is_relevant:
            return None
        
        try:
            # Determine search parameters
            timeframe_hours = decision.timeframe_hours or 24
            keywords = decision.keywords
            
            # Get relevant history
            history = self.memory_manager.get_recent_context(
                hours=timeframe_hours,
                limit=50  # Generous limit for context
            )
            
            # Filter by keywords if specified
            if keywords and history:
                filtered_history = []
                for entry in history:
                    message_lower = entry['message_content'].lower()
                    if any(keyword.lower() in message_lower for keyword in keywords):
                        filtered_history.append(entry)
                
                # If keyword filtering is too restrictive, fall back to recent history
                if len(filtered_history) < 3:
                    history = history[-20:]  # Last 20 items
                else:
                    history = filtered_history
            
            # Format context for Friday
            return self._format_context_for_friday(history, decision)
            
        except Exception as e:
            return f"Error retrieving context: {str(e)}"
    
    def _format_context_for_analysis(self, context: List[Dict]) -> str:
        """Format context for relevance analysis"""
        if not context:
            return "No recent activity."
        
        summary_items = []
        for entry in context[-5:]:  # Last 5 items for analysis
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            time_str = timestamp.strftime('%H:%M')
            
            role = entry['role']
            message = entry['message_content'][:100]  # Truncate for analysis
            
            summary_items.append(f"{time_str} {role}: {message}")
        
        return "\n".join(summary_items)
    
    def _format_context_for_friday(self, history: List[Dict], decision: RelevanceDecision) -> str:
        """Format context for Friday's consumption"""
        if not history:
            return "No relevant context found."
        
        output = ["=== RELEVANT CONVERSATION CONTEXT ==="]
        output.append(f"Relevance: {decision.reasoning}")
        output.append(f"Confidence: {decision.confidence:.1f}")
        
        if decision.suggested_context:
            output.append(f"Context: {decision.suggested_context}")
        
        output.append("\n--- Recent Timeline ---")
        
        for entry in history[-20:]:  # Last 20 relevant entries
            timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
            time_str = timestamp.strftime('%m/%d %H:%M')
            
            role_icon = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(entry['role'], "❓")
            
            message = entry['message_content']
            if len(message) > 150:
                message = message[:150] + "..."
            
            output.append(f"{time_str} {role_icon} {entry['role']}: {message}")
            
            # Add tool usage info if present
            if entry.get('tool_calls'):
                tools = entry['tool_calls']
                if isinstance(tools, dict) and tools:
                    output.append(f"    🔧 Tools used: {', '.join(tools.keys())}")
        
        output.append("=== END CONTEXT ===\n")
        
        return "\n".join(output)
    
    def _fallback_parse_response(self, response_text: str, user_message: str) -> RelevanceDecision:
        """Fallback parsing when JSON parsing fails"""
        response_lower = response_text.lower()
        
        # Simple keyword-based relevance detection
        relevance_keywords = [
            'true', 'relevant', 'yes', 'history', 'context', 'previous', 'remember'
        ]
        
        irrelevance_keywords = [
            'false', 'not relevant', 'no', 'fresh', 'new', 'independent'
        ]
        
        is_relevant = any(keyword in response_lower for keyword in relevance_keywords)
        if any(keyword in response_lower for keyword in irrelevance_keywords):
            is_relevant = False
        
        # Extract confidence if mentioned
        confidence = 0.6  # Default moderate confidence
        if 'high' in response_lower:
            confidence = 0.8
        elif 'low' in response_lower:
            confidence = 0.4
        
        return RelevanceDecision(
            is_relevant=is_relevant,
            confidence=confidence,
            reasoning=f"Fallback analysis: {response_text[:100]}...",
            timeframe_hours=24
        )
    
    def _conservative_relevance_check(self, user_message: str) -> bool:
        """Conservative keyword-based relevance check as final fallback"""
        message_lower = user_message.lower()
        
        # Strong relevance indicators
        strong_indicators = [
            'previous', 'earlier', 'before', 'last time', 'remember', 'recall',
            'you said', 'we discussed', 'continue', 'status', 'result', 'outcome'
        ]
        
        # Check for strong indicators
        return any(indicator in message_lower for indicator in strong_indicators)
    
    def analyze_conversation_flow(self, 
                                 user_message: str,
                                 conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze conversation flow and provide recommendations
        
        Args:
            user_message: The user's message
            conversation_id: Optional conversation ID for context
        
        Returns:
            Dictionary with flow analysis and recommendations
        """
        try:
            # Get recent conversation if available
            recent_history = []
            if conversation_id:
                recent_history = self.memory_manager.retrieve_history(
                    conversation_id=conversation_id,
                    limit=10
                )
            else:
                recent_history = self.memory_manager.get_recent_context(hours=2, limit=10)
            
            # Analyze conversation patterns
            analysis = {
                'message_count': len(recent_history),
                'has_tool_usage': any(entry.get('tool_calls') for entry in recent_history),
                'conversation_active': len(recent_history) > 0,
                'last_activity': None,
                'conversation_type': 'new'
            }
            
            if recent_history:
                last_entry = recent_history[-1]
                last_timestamp = datetime.fromisoformat(last_entry['timestamp'].replace('Z', '+00:00'))
                analysis['last_activity'] = last_timestamp
                
                # Determine conversation type
                time_since_last = datetime.now() - last_timestamp
                if time_since_last.total_seconds() < 300:  # 5 minutes
                    analysis['conversation_type'] = 'continuation'
                elif time_since_last.total_seconds() < 3600:  # 1 hour
                    analysis['conversation_type'] = 'recent'
                else:
                    analysis['conversation_type'] = 'distant'
            
            return analysis
            
        except Exception as e:
            return {
                'error': str(e),
                'conversation_type': 'new',
                'message_count': 0
            }

# Factory function to create relevance detector
def create_relevance_detector(memory_manager: MemoryManager, openai_client: OpenAI) -> RelevanceDetector:
    """
    Create and configure a relevance detector
    
    Args:
        memory_manager: The memory manager instance
        openai_client: OpenAI client instance
    
    Returns:
        Configured RelevanceDetector instance
    """
    return RelevanceDetector(memory_manager, openai_client)