#!/usr/bin/env python3
"""
Comprehensive test suite for Friday's memory management system
"""

import os
import sys
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import test modules
try:
    from memory_manager import MemoryManager, ConversationEntry, ToolUsageEntry
    from relevance_detector import RelevanceDetector, create_relevance_detector
    from history_retrieval import HistoryRetrieval
    from friday_with_memory import EnhancedFriday
    from openai import OpenAI
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

class MemorySystemTester:
    """Comprehensive tester for the memory management system"""
    
    def __init__(self):
        self.test_db = "test_friday_memory.db"
        self.memory_manager = None
        self.relevance_detector = None
        self.history_retrieval = None
        self.enhanced_friday = None
        self.test_results = []
        
    def setup(self):
        """Setup test environment"""
        print("🔧 Setting up test environment...")
        
        # Remove existing test database
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Initialize components
        try:
            self.memory_manager = MemoryManager(self.test_db)
            
            # Only create OpenAI-dependent components if API key is available
            if os.getenv("OPENAI_API_KEY"):
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.relevance_detector = create_relevance_detector(self.memory_manager, client)
                self.enhanced_friday = EnhancedFriday(self.test_db)
            
            self.history_retrieval = HistoryRetrieval(self.memory_manager)
            
            print("✅ Test environment setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup test environment"""
        print("🧹 Cleaning up test environment...")
        
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        print("✅ Cleanup complete")
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results"""
        print(f"\n🧪 Running test: {test_name}")
        
        try:
            start_time = time.time()
            result = test_func()
            execution_time = time.time() - start_time
            
            if result:
                print(f"✅ {test_name} PASSED ({execution_time:.2f}s)")
                self.test_results.append((test_name, True, execution_time, None))
                return True
            else:
                print(f"❌ {test_name} FAILED ({execution_time:.2f}s)")
                self.test_results.append((test_name, False, execution_time, "Test returned False"))
                return False
                
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            self.test_results.append((test_name, False, 0, str(e)))
            return False
    
    def test_memory_manager_basic(self) -> bool:
        """Test basic memory manager functionality"""
        # Test session creation
        session_id = self.memory_manager.create_conversation_session("Test Session")
        if not session_id:
            return False
        
        # Test conversation storage
        entry = ConversationEntry(
            id="test-1",
            timestamp=datetime.now(),
            conversation_id=session_id,
            role="user",
            message_content="Hello, this is a test message",
            sequence_number=1
        )
        
        stored_id = self.memory_manager.store_conversation(entry)
        if not stored_id:
            return False
        
        # Test retrieval
        history = self.memory_manager.retrieve_history(conversation_id=session_id)
        if len(history) != 1:
            return False
        
        if history[0]['message_content'] != "Hello, this is a test message":
            return False
        
        return True
    
    def test_timeline_storage(self) -> bool:
        """Test timeline-based storage with proper sequencing"""
        session_id = self.memory_manager.create_conversation_session("Timeline Test")
        
        # Store multiple messages with different timestamps
        base_time = datetime.now()
        messages = [
            ("user", "First message", 1),
            ("assistant", "First response", 2),
            ("user", "Second message", 3),
            ("assistant", "Second response", 4)
        ]
        
        for i, (role, content, seq) in enumerate(messages):
            entry = ConversationEntry(
                id=f"timeline-{i}",
                timestamp=base_time + timedelta(seconds=i*10),
                conversation_id=session_id,
                role=role,
                message_content=content,
                sequence_number=seq
            )
            self.memory_manager.store_conversation(entry)
        
        # Retrieve and verify timeline order
        history = self.memory_manager.retrieve_history(conversation_id=session_id)
        
        if len(history) != 4:
            return False
        
        # Check chronological order
        for i in range(len(history) - 1):
            current_time = datetime.fromisoformat(history[i]['timestamp'].replace('Z', '+00:00'))
            next_time = datetime.fromisoformat(history[i+1]['timestamp'].replace('Z', '+00:00'))
            if current_time > next_time:
                return False
        
        # Check sequence numbers
        expected_sequences = [1, 2, 3, 4]
        actual_sequences = [entry['sequence_number'] for entry in history]
        if actual_sequences != expected_sequences:
            return False
        
        return True
    
    def test_tool_usage_tracking(self) -> bool:
        """Test tool usage tracking in timeline"""
        session_id = self.memory_manager.create_conversation_session("Tool Test")
        
        # Store tool usage
        tool_entry = ToolUsageEntry(
            id="tool-test-1",
            timestamp=datetime.now(),
            conversation_id=session_id,
            tool_name="send_email",
            parameters={"to": "test@example.com", "subject": "Test", "body": "Test body"},
            result="Email sent successfully",
            execution_time=1.5
        )
        
        stored_id = self.memory_manager.store_tool_usage(tool_entry)
        if not stored_id:
            return False
        
        # Retrieve tool usage
        tool_history = self.memory_manager.get_tool_usage_timeline(tool_name="send_email")
        
        if len(tool_history) != 1:
            return False
        
        entry = tool_history[0]
        if entry['tool_name'] != "send_email":
            return False
        
        if entry['parameters']['to'] != "test@example.com":
            return False
        
        if entry['result'] != "Email sent successfully":
            return False
        
        return True
    
    def test_history_retrieval_filtering(self) -> bool:
        """Test history retrieval with various filters"""
        session_id = self.memory_manager.create_conversation_session("Filter Test")
        
        # Create test data with different characteristics
        base_time = datetime.now()
        test_entries = [
            ("user", "Hello Friday", 1, None),
            ("assistant", "Hello sir, how may I assist you?", 2, None),
            ("user", "Send an email please", 3, None),
            ("assistant", "I'll send the email now", 4, {"send_email": {"to": "test@example.com"}}),
            ("user", "Check the weather", 5, None),
            ("assistant", "I'll check the weather for you", 6, {"weather_check": {"location": "New York"}})
        ]
        
        for i, (role, content, seq, tools) in enumerate(test_entries):
            entry = ConversationEntry(
                id=f"filter-{i}",
                timestamp=base_time + timedelta(minutes=i*5),
                conversation_id=session_id,
                role=role,
                message_content=content,
                tool_calls=tools,
                sequence_number=seq
            )
            self.memory_manager.store_conversation(entry)
        
        # Test keyword filtering
        email_results = self.memory_manager.retrieve_history(
            conversation_id=session_id,
            keywords=["email"]
        )
        
        # Should find entries mentioning email
        if len(email_results) < 2:
            return False
        
        # Test role filtering
        user_results = self.memory_manager.retrieve_history(
            conversation_id=session_id,
            role_filter="user"
        )
        
        # Should find only user messages
        if len(user_results) != 3:
            return False
        
        for entry in user_results:
            if entry['role'] != 'user':
                return False
        
        # Test limit
        limited_results = self.memory_manager.retrieve_history(
            conversation_id=session_id,
            limit=2
        )
        
        if len(limited_results) != 2:
            return False
        
        return True
    
    def test_timeframe_search(self) -> bool:
        """Test searching by timeframe"""
        session_id = self.memory_manager.create_conversation_session("Timeframe Test")
        
        # Create entries at different times
        now = datetime.now()
        times = [
            now - timedelta(hours=25),  # More than 24 hours ago
            now - timedelta(hours=12),  # 12 hours ago
            now - timedelta(hours=2),   # 2 hours ago
            now - timedelta(minutes=30) # 30 minutes ago
        ]
        
        for i, timestamp in enumerate(times):
            entry = ConversationEntry(
                id=f"time-{i}",
                timestamp=timestamp,
                conversation_id=session_id,
                role="user" if i % 2 == 0 else "assistant",
                message_content=f"Message from {timestamp.strftime('%H:%M')}",
                sequence_number=i + 1
            )
            self.memory_manager.store_conversation(entry)
        
        # Test with specific session to avoid interference from other tests
        session_recent = self.memory_manager.retrieve_history(
            conversation_id=session_id,
            start_time=now - timedelta(hours=24)
        )
        
        # Should exclude the 25-hour-old entry (expect 3 entries within 24 hours)
        if len(session_recent) != 3:
            return False
        
        # Test 1-hour timeframe with session filter
        session_very_recent = self.memory_manager.retrieve_history(
            conversation_id=session_id,
            start_time=now - timedelta(hours=1)
        )
        
        # Should only include the 30-minute-old entry
        if len(session_very_recent) != 1:
            return False
        
        return True
    
    def test_history_retrieval_functions(self) -> bool:
        """Test the history retrieval function interface"""
        session_id = self.memory_manager.create_conversation_session("Interface Test")
        
        # Add some test data
        now = datetime.now()
        test_data = [
            ("user", "Tell me about the weather", 1),
            ("assistant", "I'll check the weather for you", 2),
            ("user", "Send an email to John", 3),
            ("assistant", "I'll send the email now", 4)
        ]
        
        for i, (role, content, seq) in enumerate(test_data):
            entry = ConversationEntry(
                id=f"interface-{i}",
                timestamp=now + timedelta(minutes=i),
                conversation_id=session_id,
                role=role,
                message_content=content,
                sequence_number=seq
            )
            self.memory_manager.store_conversation(entry)
        
        # Test retrieve_history function
        result = self.history_retrieval.retrieve_history(
            timeframe="hours",
            timeframe_value=1,
            limit=10
        )
        
        if "CONVERSATION TIMELINE" not in result:
            return False
        
        if "weather" not in result.lower():
            return False
        
        # Test search by keywords
        email_result = self.history_retrieval.retrieve_history(
            keywords="email",
            limit=5
        )
        
        if "email" not in email_result.lower():
            return False
        
        return True
    
    def test_relevance_detection(self) -> bool:
        """Test relevance detection system (if OpenAI API is available)"""
        if not self.relevance_detector:
            print("⚠️  Skipping relevance detection test (no OpenAI API key)")
            return True
        
        session_id = self.memory_manager.create_conversation_session("Relevance Test")
        
        # Add some context
        entry = ConversationEntry(
            id="relevance-1",
            timestamp=datetime.now() - timedelta(minutes=5),
            conversation_id=session_id,
            role="user",
            message_content="Please send an email to john@example.com",
            sequence_number=1
        )
        self.memory_manager.store_conversation(entry)
        
        # Test messages that should trigger relevance (high confidence cases)
        relevant_messages = [
            "Did you send that email?",
            "What was the result of my previous request?",
            "How did the email sending go?"
        ]
        
        # Test messages that should not trigger relevance
        irrelevant_messages = [
            "What's the weather like?",
            "Tell me a joke",
            "What can you do?"
        ]
        
        try:
            # Count successful relevance detections
            relevant_detected = 0
            for msg in relevant_messages:
                decision = self.relevance_detector.analyze_relevance(msg)
                if decision.is_relevant and decision.confidence > 0.5:
                    relevant_detected += 1
            
            # Should detect at least 2 out of 3 relevant messages
            if relevant_detected < 2:
                print(f"❌ Only detected {relevant_detected}/3 relevant messages")
                return False
            
            # Test irrelevant messages - should mostly be irrelevant
            irrelevant_detected = 0
            for msg in irrelevant_messages:
                decision = self.relevance_detector.analyze_relevance(msg)
                if not decision.is_relevant or decision.confidence <= 0.6:
                    irrelevant_detected += 1
            
            # Should detect at least 2 out of 3 irrelevant messages as irrelevant
            if irrelevant_detected < 2:
                print(f"❌ Only detected {irrelevant_detected}/3 irrelevant messages as irrelevant")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Relevance detection failed: {e}")
            return False
    
    def test_enhanced_friday_integration(self) -> bool:
        """Test the enhanced Friday integration (if OpenAI API is available)"""
        if not self.enhanced_friday:
            print("⚠️  Skipping Enhanced Friday test (no OpenAI API key)")
            return True
        
        try:
            # Start a session
            session_id = self.enhanced_friday.start_conversation_session("Integration Test")
            if not session_id:
                return False
            
            # Test basic interaction (this will call OpenAI)
            response = self.enhanced_friday.get_response("Hello Friday, what can you help me with?")
            
            if not response or len(response) < 10:
                return False
            
            # Check if conversation was stored
            stats = self.enhanced_friday.get_memory_stats()
            if stats['total_conversations'] < 2:  # Should have user + assistant messages
                return False
            
            # End session
            self.enhanced_friday.end_conversation_session("Test completed")
            
            return True
            
        except Exception as e:
            print(f"❌ Enhanced Friday integration failed: {e}")
            return False
    
    def test_database_integrity(self) -> bool:
        """Test database integrity and constraints"""
        try:
            # Check database structure
            with sqlite3.connect(self.test_db) as conn:
                cursor = conn.cursor()
                
                # Check if all tables exist
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ['conversations', 'conversation_sessions', 'tool_usage_log']
                for table in expected_tables:
                    if table not in tables:
                        print(f"❌ Missing table: {table}")
                        return False
                
                # Check indexes
                cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                indexes = [row[0] for row in cursor.fetchall()]
                
                expected_indexes = [
                    'idx_conversations_timestamp',
                    'idx_conversations_conversation_id',
                    'idx_tool_usage_timestamp'
                ]
                
                for index in expected_indexes:
                    if index not in indexes:
                        print(f"❌ Missing index: {index}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"❌ Database integrity check failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report"""
        print("🚀 Starting Friday Memory System Test Suite")
        print("=" * 60)
        
        if not self.setup():
            print("❌ Setup failed, aborting tests")
            return False
        
        # Define tests
        tests = [
            ("Database Integrity", self.test_database_integrity),
            ("Memory Manager Basic", self.test_memory_manager_basic),
            ("Timeline Storage", self.test_timeline_storage),
            ("Tool Usage Tracking", self.test_tool_usage_tracking),
            ("History Filtering", self.test_history_retrieval_filtering),
            ("Timeframe Search", self.test_timeframe_search),
            ("History Retrieval Functions", self.test_history_retrieval_functions),
            ("Relevance Detection", self.test_relevance_detection),
            ("Enhanced Friday Integration", self.test_enhanced_friday_integration)
        ]
        
        # Run tests
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
        
        # Generate report
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for test_name, success, exec_time, error in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {test_name} ({exec_time:.2f}s)")
            if error:
                print(f"    Error: {error}")
        
        # Memory stats
        if self.memory_manager:
            print("\n💾 Memory Database Stats:")
            stats = self.memory_manager.get_database_stats()
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        self.cleanup()
        
        if passed == total:
            print("\n🎉 All tests passed! Memory system is working correctly.")
            return True
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues above.")
            return False

def main():
    """Run the test suite"""
    tester = MemorySystemTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()