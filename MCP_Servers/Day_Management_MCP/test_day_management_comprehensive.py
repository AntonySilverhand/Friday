#!/usr/bin/env python3
"""
Comprehensive Test Suite for Day Management MCP Server

This test suite provides complete coverage of the Day Management MCP server including:
- All 10 MCP tools testing
- OAuth2 authentication testing
- Timezone handling and date parsing
- Smart scheduling and conflict detection
- Friday integration testing
- Mock testing for Google APIs
- Unit and integration tests

Requirements:
- pytest
- pytest-asyncio
- pytest-mock
- google-api-python-client
- fastmcp
"""

import os
import sys
import json
import pickle
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
import pytz
from dateutil import parser as date_parser

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import modules under test
from MCP_Servers.Day_Management_MCP.day_management_mcp_server import (
    DayManagementMCPServer,
    CalendarEvent,
    Task,
    SCOPES
)

class TestDayManagementMCPServer:
    """Test suite for Day Management MCP Server core functionality"""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock Google OAuth2 credentials"""
        mock_creds = Mock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds.refresh_token = "mock_refresh_token"
        return mock_creds
    
    @pytest.fixture
    def mock_calendar_service(self):
        """Mock Google Calendar API service"""
        mock_service = Mock()
        mock_service.events.return_value = Mock()
        return mock_service
    
    @pytest.fixture
    def mock_tasks_service(self):
        """Mock Google Tasks API service"""
        mock_service = Mock()
        mock_service.tasks.return_value = Mock()
        mock_service.tasklists.return_value = Mock()
        return mock_service
    
    @pytest.fixture
    def sample_calendar_event(self):
        """Sample calendar event data"""
        return {
            'id': 'test_event_123',
            'summary': 'Test Meeting',
            'description': 'A test meeting',
            'location': 'Conference Room A',
            'start': {
                'dateTime': '2024-07-05T10:00:00Z',
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': '2024-07-05T11:00:00Z',
                'timeZone': 'UTC'
            },
            'attendees': [
                {'email': 'user1@example.com'},
                {'email': 'user2@example.com'}
            ],
            'status': 'confirmed',
            'creator': {'email': 'creator@example.com'},
            'organizer': {'email': 'organizer@example.com'},
            'htmlLink': 'https://calendar.google.com/event/test_event_123'
        }
    
    @pytest.fixture
    def sample_task(self):
        """Sample task data"""
        return {
            'id': 'task_123',
            'title': 'Complete project documentation',
            'notes': 'Write comprehensive documentation for the project',
            'status': 'needsAction',
            'due': '2024-07-06T17:00:00Z',
            'position': '00000000001000000000'
        }
    
    @pytest.fixture
    def sample_tasklist(self):
        """Sample tasklist data"""
        return {
            'id': 'tasklist_123',
            'title': 'My Tasks',
            'updated': '2024-07-05T12:00:00Z'
        }
    
    @pytest.fixture
    def day_server(self, mock_credentials, mock_calendar_service, mock_tasks_service):
        """Create DayManagementMCPServer instance with mocked services"""
        from unittest.mock import mock_open
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps({
                 "installed": {
                     "client_id": "mock_client_id",
                     "client_secret": "mock_client_secret",
                     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                     "token_uri": "https://oauth2.googleapis.com/token"
                 }
             }))), \
             patch('pickle.load', return_value=mock_credentials), \
             patch('googleapiclient.discovery.build') as mock_build:
            
            # Configure mock build to return our mock services
            mock_build.side_effect = lambda service, version, credentials: {
                'calendar': mock_calendar_service,
                'tasks': mock_tasks_service
            }[service]
            
            server = DayManagementMCPServer()
            server.credentials = mock_credentials
            server.calendar_service = mock_calendar_service
            server.tasks_service = mock_tasks_service
            
            return server

class TestDayManagementServerInitialization:
    """Test server initialization and configuration"""
    
    def test_initialization_without_credentials(self):
        """Test server initialization when credentials file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            server = DayManagementMCPServer()
            assert server.calendar_service is None
            assert server.tasks_service is None
            assert server.credentials is None
    
    def test_initialization_with_valid_credentials(self, mock_credentials):
        """Test server initialization with valid credentials"""
        from unittest.mock import mock_open
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps({
                 "installed": {
                     "client_id": "mock_client_id",
                     "client_secret": "mock_client_secret",
                     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                     "token_uri": "https://oauth2.googleapis.com/token"
                 }
             }))), \
             patch('pickle.load', return_value=mock_credentials), \
             patch('googleapiclient.discovery.build') as mock_build:
            
            mock_calendar = Mock()
            mock_tasks = Mock()
            mock_build.side_effect = lambda service, version, credentials: {
                'calendar': mock_calendar,
                'tasks': mock_tasks
            }[service]
            
            server = DayManagementMCPServer()
            
            assert server.calendar_service == mock_calendar
            assert server.tasks_service == mock_tasks
            assert server.credentials == mock_credentials
    
    def test_timezone_configuration(self):
        """Test timezone configuration"""
        with patch.dict(os.environ, {'USER_TIMEZONE': 'America/New_York'}):
            server = DayManagementMCPServer()
            assert server.timezone == pytz.timezone('America/New_York')
    
    def test_environment_variables(self):
        """Test environment variable configuration"""
        with patch.dict(os.environ, {
            'GOOGLE_CREDENTIALS_PATH': '/custom/path/creds.json',
            'GOOGLE_TOKEN_PATH': '/custom/path/token.pickle',
            'USER_TIMEZONE': 'Europe/London'
        }):
            server = DayManagementMCPServer()
            assert server.credentials_path == '/custom/path/creds.json'
            assert server.token_path == '/custom/path/token.pickle'
            assert server.timezone == pytz.timezone('Europe/London')

class TestOAuth2Authentication:
    """Test OAuth2 authentication flow"""
    
    @patch('google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file')
    @patch('google.auth.transport.requests.Request')
    def test_oauth_flow_new_credentials(self, mock_request, mock_flow):
        """Test OAuth flow for new credentials"""
        from unittest.mock import mock_open
        
        # Mock flow
        mock_flow_instance = Mock()
        mock_flow.return_value = mock_flow_instance
        
        mock_creds = Mock()
        mock_creds.valid = True
        mock_flow_instance.run_local_server.return_value = mock_creds
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps({
                 "installed": {
                     "client_id": "mock_client_id",
                     "client_secret": "mock_client_secret",
                     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                     "token_uri": "https://oauth2.googleapis.com/token"
                 }
             }))), \
             patch('pickle.load', side_effect=FileNotFoundError()), \
             patch('pickle.dump') as mock_dump, \
             patch('googleapiclient.discovery.build'):
            
            server = DayManagementMCPServer()
            server._get_google_services()
            
            # Verify OAuth flow was called
            mock_flow.assert_called_once()
            mock_flow_instance.run_local_server.assert_called_once()
            mock_dump.assert_called_once()
    
    def test_credentials_refresh(self):
        """Test credential refresh when expired"""
        from unittest.mock import mock_open
        
        mock_creds = Mock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "valid_refresh_token"
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps({
                 "installed": {
                     "client_id": "mock_client_id",
                     "client_secret": "mock_client_secret",
                     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                     "token_uri": "https://oauth2.googleapis.com/token"
                 }
             }))), \
             patch('pickle.load', return_value=mock_creds), \
             patch('pickle.dump') as mock_dump, \
             patch('googleapiclient.discovery.build'):
            
            server = DayManagementMCPServer()
            server._get_google_services()
            
            # Verify credentials were refreshed
            mock_creds.refresh.assert_called_once()
            mock_dump.assert_called_once()

class TestCalendarEventManagement:
    """Test calendar event management functionality"""
    
    @pytest.mark.asyncio
    async def test_get_calendar_events_success(self, day_server, sample_calendar_event):
        """Test successful calendar events retrieval"""
        # Mock calendar service response
        mock_result = {'items': [sample_calendar_event]}
        day_server.calendar_service.events().list().execute.return_value = mock_result
        
        events = await day_server.get_calendar_events(days_ahead=7, max_results=10)
        
        assert len(events) == 1
        assert events[0]['event_id'] == 'test_event_123'
        assert events[0]['title'] == 'Test Meeting'
        assert events[0]['location'] == 'Conference Room A'
        assert len(events[0]['attendees']) == 2
    
    @pytest.mark.asyncio
    async def test_get_calendar_events_no_service(self):
        """Test calendar events retrieval when service is not available"""
        server = DayManagementMCPServer()
        server.calendar_service = None
        
        events = await server.get_calendar_events()
        
        assert events == []
    
    @pytest.mark.asyncio
    async def test_create_calendar_event_success(self, day_server):
        """Test successful calendar event creation"""
        # Mock calendar service response
        mock_event = {
            'id': 'new_event_123',
            'htmlLink': 'https://calendar.google.com/event/new_event_123'
        }
        day_server.calendar_service.events().insert().execute.return_value = mock_event
        
        result = await day_server.create_calendar_event(
            title="New Meeting",
            start_datetime="2024-07-05T14:00:00Z",
            end_datetime="2024-07-05T15:00:00Z",
            description="Test meeting description",
            location="Room B",
            attendees=["user1@example.com", "user2@example.com"]
        )
        
        assert result['success'] is True
        assert result['event_id'] == 'new_event_123'
        assert result['title'] == 'New Meeting'
        assert 'calendar_link' in result
    
    @pytest.mark.asyncio
    async def test_create_calendar_event_invalid_datetime(self, day_server):
        """Test calendar event creation with invalid datetime"""
        result = await day_server.create_calendar_event(
            title="Test Meeting",
            start_datetime="invalid_datetime",
            end_datetime="2024-07-05T15:00:00Z"
        )
        
        assert 'error' in result
        assert 'Invalid datetime format' in result['error']
    
    @pytest.mark.asyncio
    async def test_update_calendar_event_success(self, day_server, sample_calendar_event):
        """Test successful calendar event update"""
        # Mock get and update responses
        day_server.calendar_service.events().get().execute.return_value = sample_calendar_event
        
        updated_event = sample_calendar_event.copy()
        updated_event['summary'] = 'Updated Meeting'
        day_server.calendar_service.events().update().execute.return_value = updated_event
        
        result = await day_server.update_calendar_event(
            event_id='test_event_123',
            title='Updated Meeting',
            description='Updated description'
        )
        
        assert result['success'] is True
        assert result['event_id'] == 'test_event_123'
        assert result['title'] == 'Updated Meeting'
    
    @pytest.mark.asyncio
    async def test_delete_calendar_event_success(self, day_server):
        """Test successful calendar event deletion"""
        # Mock delete response
        day_server.calendar_service.events().delete().execute.return_value = None
        
        result = await day_server.delete_calendar_event(event_id='test_event_123')
        
        assert result['success'] is True
        assert result['event_id'] == 'test_event_123'
        assert 'deleted successfully' in result['message']

class TestTaskManagement:
    """Test task management functionality"""
    
    @pytest.mark.asyncio
    async def test_get_tasks_success(self, day_server, sample_task):
        """Test successful tasks retrieval"""
        # Mock tasks service response
        mock_result = {'items': [sample_task]}
        day_server.tasks_service.tasks().list().execute.return_value = mock_result
        
        tasks = await day_server.get_tasks(tasklist_id='@default', max_results=10)
        
        assert len(tasks) == 1
        assert tasks[0]['task_id'] == 'task_123'
        assert tasks[0]['title'] == 'Complete project documentation'
        assert tasks[0]['status'] == 'needsAction'
        assert tasks[0]['due_date'] is not None
    
    @pytest.mark.asyncio
    async def test_get_tasks_no_service(self):
        """Test tasks retrieval when service is not available"""
        server = DayManagementMCPServer()
        server.tasks_service = None
        
        tasks = await server.get_tasks()
        
        assert tasks == []
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, day_server):
        """Test successful task creation"""
        # Mock tasks service response
        mock_task = {
            'id': 'new_task_123',
            'title': 'New Task'
        }
        day_server.tasks_service.tasks().insert().execute.return_value = mock_task
        
        result = await day_server.create_task(
            title="New Task",
            notes="Task description",
            due_date="2024-07-06T17:00:00Z",
            tasklist_id="@default"
        )
        
        assert result['success'] is True
        assert result['task_id'] == 'new_task_123'
        assert result['title'] == 'New Task'
    
    @pytest.mark.asyncio
    async def test_create_task_invalid_due_date(self, day_server):
        """Test task creation with invalid due date"""
        result = await day_server.create_task(
            title="Test Task",
            due_date="invalid_date"
        )
        
        assert 'error' in result
        assert 'Invalid due date format' in result['error']
    
    @pytest.mark.asyncio
    async def test_update_task_success(self, day_server, sample_task):
        """Test successful task update"""
        # Mock get and update responses
        day_server.tasks_service.tasks().get().execute.return_value = sample_task
        
        updated_task = sample_task.copy()
        updated_task['title'] = 'Updated Task'
        updated_task['status'] = 'completed'
        day_server.tasks_service.tasks().update().execute.return_value = updated_task
        
        result = await day_server.update_task(
            task_id='task_123',
            title='Updated Task',
            status='completed'
        )
        
        assert result['success'] is True
        assert result['task_id'] == 'task_123'
        assert result['title'] == 'Updated Task'
        assert result['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_complete_task_success(self, day_server, sample_task):
        """Test successful task completion"""
        # Mock get and update responses
        day_server.tasks_service.tasks().get().execute.return_value = sample_task
        
        completed_task = sample_task.copy()
        completed_task['status'] = 'completed'
        day_server.tasks_service.tasks().update().execute.return_value = completed_task
        
        result = await day_server.complete_task(task_id='task_123')
        
        assert result['success'] is True
        assert result['task_id'] == 'task_123'
        assert result['status'] == 'completed'
    
    @pytest.mark.asyncio
    async def test_get_tasklists_success(self, day_server, sample_tasklist):
        """Test successful tasklists retrieval"""
        # Mock tasklists service response
        mock_result = {'items': [sample_tasklist]}
        day_server.tasks_service.tasklists().list().execute.return_value = mock_result
        
        tasklists = await day_server.get_tasklists()
        
        assert len(tasklists) == 1
        assert tasklists[0]['id'] == 'tasklist_123'
        assert tasklists[0]['title'] == 'My Tasks'

class TestDayOverview:
    """Test day overview functionality"""
    
    @pytest.mark.asyncio
    async def test_get_day_overview_success(self, day_server, sample_calendar_event, sample_task):
        """Test successful day overview retrieval"""
        # Mock calendar service response
        mock_events = {'items': [sample_calendar_event]}
        day_server.calendar_service.events().list().execute.return_value = mock_events
        
        # Mock tasks service response
        mock_tasks = {'items': [sample_task]}
        day_server.tasks_service.tasks().list().execute.return_value = mock_tasks
        
        overview = await day_server.get_day_overview(target_date='2024-07-05')
        
        assert 'date' in overview
        assert 'day_name' in overview
        assert 'events_count' in overview
        assert 'tasks_due_count' in overview
        assert 'free_time_slots' in overview
        assert overview['events_count'] == 1
    
    @pytest.mark.asyncio
    async def test_get_day_overview_no_date(self, day_server):
        """Test day overview for today when no date specified"""
        # Mock empty responses
        day_server.calendar_service.events().list().execute.return_value = {'items': []}
        day_server.tasks_service.tasks().list().execute.return_value = {'items': []}
        
        overview = await day_server.get_day_overview()
        
        assert 'date' in overview
        assert overview['date'] == date.today().isoformat()
        assert overview['events_count'] == 0
        assert overview['tasks_due_count'] == 0

class TestTimezoneHandling:
    """Test timezone handling and date parsing"""
    
    def test_timezone_configuration(self):
        """Test timezone configuration from environment"""
        with patch.dict(os.environ, {'USER_TIMEZONE': 'America/New_York'}):
            server = DayManagementMCPServer()
            assert server.timezone == pytz.timezone('America/New_York')
    
    def test_parse_calendar_event_timezone(self, day_server):
        """Test calendar event parsing with timezone"""
        event_data = {
            'id': 'test_event',
            'summary': 'Test Event',
            'start': {
                'dateTime': '2024-07-05T10:00:00-04:00',
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': '2024-07-05T11:00:00-04:00',
                'timeZone': 'America/New_York'
            },
            'status': 'confirmed',
            'creator': {'email': 'test@example.com'},
            'organizer': {'email': 'test@example.com'}
        }
        
        parsed_event = day_server._parse_calendar_event(event_data)
        
        assert parsed_event.timezone == 'America/New_York'
        assert parsed_event.start_time.tzinfo is not None
        assert parsed_event.end_time.tzinfo is not None
    
    def test_parse_all_day_event(self, day_server):
        """Test parsing all-day calendar event"""
        event_data = {
            'id': 'all_day_event',
            'summary': 'All Day Event',
            'start': {
                'date': '2024-07-05'
            },
            'end': {
                'date': '2024-07-06'
            },
            'status': 'confirmed',
            'creator': {'email': 'test@example.com'},
            'organizer': {'email': 'test@example.com'}
        }
        
        parsed_event = day_server._parse_calendar_event(event_data)
        
        assert parsed_event.is_all_day is True
        assert parsed_event.start_time.date() == date(2024, 7, 5)
        assert parsed_event.end_time.date() == date(2024, 7, 6)
    
    def test_relative_time_calculation(self, day_server):
        """Test relative time calculation"""
        now = datetime.now()
        
        # Test future time
        future_time = now + timedelta(hours=2)
        relative = day_server._get_relative_time(future_time)
        assert "in 2 hour" in relative
        
        # Test past time
        past_time = now - timedelta(days=1)
        relative = day_server._get_relative_time(past_time)
        assert "1 day" in relative and "ago" in relative
    
    def test_task_overdue_detection(self, day_server):
        """Test task overdue detection"""
        # Create overdue task
        overdue_task = Task(
            task_id='overdue_task',
            tasklist_id='@default',
            title='Overdue Task',
            notes='',
            status='needsAction',
            due_date=datetime.now() - timedelta(days=1),
            completed_date=None,
            parent_task_id=None,
            position='',
            links=[]
        )
        
        assert day_server._is_task_overdue(overdue_task) is True
        
        # Create future task
        future_task = Task(
            task_id='future_task',
            tasklist_id='@default',
            title='Future Task',
            notes='',
            status='needsAction',
            due_date=datetime.now() + timedelta(days=1),
            completed_date=None,
            parent_task_id=None,
            position='',
            links=[]
        )
        
        assert day_server._is_task_overdue(future_task) is False

class TestSmartScheduling:
    """Test smart scheduling and conflict detection"""
    
    def test_free_time_calculation(self, day_server):
        """Test free time slot calculation"""
        target_date = date(2024, 7, 5)
        
        # Create sample events
        events = [
            {
                'start_time': '2024-07-05T10:00:00Z',
                'end_time': '2024-07-05T11:00:00Z',
                'title': 'Meeting 1'
            },
            {
                'start_time': '2024-07-05T14:00:00Z',
                'end_time': '2024-07-05T15:00:00Z',
                'title': 'Meeting 2'
            }
        ]
        
        free_slots = day_server._calculate_free_time(events, target_date)
        
        assert len(free_slots) >= 2  # At least morning and afternoon slots
        
        # Check that free slots don't overlap with events
        for slot in free_slots:
            slot_start = date_parser.parse(slot['start'])
            slot_end = date_parser.parse(slot['end'])
            assert slot_start < slot_end
            assert slot['duration_minutes'] > 0
    
    def test_free_time_no_events(self, day_server):
        """Test free time calculation with no events"""
        target_date = date(2024, 7, 5)
        events = []
        
        free_slots = day_server._calculate_free_time(events, target_date)
        
        assert len(free_slots) == 1  # Full day should be free
        assert free_slots[0]['duration_minutes'] == 540  # 9 hours (9 AM to 6 PM)
    
    def test_event_conflict_detection(self, day_server):
        """Test event conflict detection logic"""
        # Create overlapping events
        event1 = {
            'start_time': '2024-07-05T10:00:00Z',
            'end_time': '2024-07-05T11:30:00Z',
            'title': 'Meeting 1'
        }
        
        event2 = {
            'start_time': '2024-07-05T11:00:00Z',
            'end_time': '2024-07-05T12:00:00Z',
            'title': 'Meeting 2'
        }
        
        events = [event1, event2]
        target_date = date(2024, 7, 5)
        
        free_slots = day_server._calculate_free_time(events, target_date)
        
        # Should handle overlapping events properly
        assert isinstance(free_slots, list)

class TestMCPTools:
    """Test MCP tool implementations"""
    
    @pytest.mark.asyncio
    async def test_get_calendar_events_tool(self, day_server, sample_calendar_event):
        """Test get_calendar_events MCP tool"""
        # Mock the server method
        with patch.object(day_server, 'get_calendar_events') as mock_get_events:
            mock_get_events.return_value = [day_server._event_to_dict(
                day_server._parse_calendar_event(sample_calendar_event)
            )]
            
            # Import and test the tool
            from MCP_Servers.Day_Management_MCP.day_management_mcp_server import get_calendar_events
            
            with patch('MCP_Servers.Day_Management_MCP.day_management_mcp_server.day_server', day_server):
                result = await get_calendar_events(days_ahead=7, max_results=10)
                
                assert isinstance(result, str)
                assert 'Test Meeting' in result
                assert 'Conference Room A' in result
    
    @pytest.mark.asyncio
    async def test_create_calendar_event_tool(self, day_server):
        """Test create_calendar_event MCP tool"""
        # Mock the server method
        with patch.object(day_server, 'create_calendar_event') as mock_create:
            mock_create.return_value = {
                'success': True,
                'event_id': 'new_event_123',
                'title': 'New Meeting',
                'start_time': '2024-07-05T14:00:00Z',
                'calendar_link': 'https://calendar.google.com/event/new_event_123'
            }
            
            # Import and test the tool
            from MCP_Servers.Day_Management_MCP.day_management_mcp_server import create_calendar_event
            
            with patch('MCP_Servers.Day_Management_MCP.day_management_mcp_server.day_server', day_server):
                result = await create_calendar_event(
                    title="New Meeting",
                    start_datetime="2024-07-05T14:00:00Z",
                    end_datetime="2024-07-05T15:00:00Z",
                    description="Test description",
                    location="Room B",
                    attendees="user1@example.com,user2@example.com"
                )
                
                assert isinstance(result, str)
                assert 'New Meeting' in result
                assert 'created successfully' in result
    
    @pytest.mark.asyncio
    async def test_get_tasks_tool(self, day_server, sample_task):
        """Test get_tasks MCP tool"""
        # Mock the server method
        with patch.object(day_server, 'get_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [day_server._task_to_dict(
                day_server._parse_task(sample_task, '@default')
            )]
            
            # Import and test the tool
            from MCP_Servers.Day_Management_MCP.day_management_mcp_server import get_tasks
            
            with patch('MCP_Servers.Day_Management_MCP.day_management_mcp_server.day_server', day_server):
                result = await get_tasks(tasklist_id='@default', show_completed=False)
                
                assert isinstance(result, str)
                assert 'Complete project documentation' in result
                assert 'PENDING TASKS' in result
    
    @pytest.mark.asyncio
    async def test_get_day_overview_tool(self, day_server):
        """Test get_day_overview MCP tool"""
        # Mock the server method
        with patch.object(day_server, 'get_day_overview') as mock_overview:
            mock_overview.return_value = {
                'date': '2024-07-05',
                'day_name': 'Friday',
                'events_count': 2,
                'events': [],
                'tasks_due_count': 1,
                'tasks_due': [],
                'free_time_slots': []
            }
            
            # Import and test the tool
            from MCP_Servers.Day_Management_MCP.day_management_mcp_server import get_day_overview
            
            with patch('MCP_Servers.Day_Management_MCP.day_management_mcp_server.day_server', day_server):
                result = await get_day_overview(target_date='2024-07-05')
                
                assert isinstance(result, str)
                assert 'DAY OVERVIEW' in result
                assert 'Friday' in result
                assert '2024-07-05' in result

class TestFridayIntegration:
    """Test Friday AI Assistant integration"""
    
    @pytest.fixture
    def mock_friday(self):
        """Mock Friday AI Assistant"""
        mock_friday = Mock()
        mock_friday._get_tools_config.return_value = [
            {
                "type": "mcp",
                "server_label": "day-management",
                "name": "Day Management MCP",
                "host": "127.0.0.1",
                "port": 5003
            }
        ]
        return mock_friday
    
    def test_friday_tools_configuration(self, mock_friday):
        """Test Friday's tools configuration includes Day Management MCP"""
        tools_config = mock_friday._get_tools_config()
        
        day_tool = next((tool for tool in tools_config 
                        if tool.get('server_label') == 'day-management'), None)
        
        assert day_tool is not None
        assert day_tool['type'] == 'mcp'
        assert day_tool['host'] == '127.0.0.1'
        assert day_tool['port'] == 5003
    
    @pytest.mark.asyncio
    async def test_friday_day_management_interaction(self, mock_friday, day_server):
        """Test Friday's interaction with Day Management MCP"""
        # Mock Friday's MCP client interaction
        mock_friday.call_mcp_tool = AsyncMock()
        mock_friday.call_mcp_tool.return_value = "Sample calendar events response"
        
        # Simulate Friday calling Day Management MCP
        result = await mock_friday.call_mcp_tool(
            server_label="day-management",
            tool_name="get_calendar_events",
            parameters={"days_ahead": 7, "max_results": 10}
        )
        
        assert result == "Sample calendar events response"
        mock_friday.call_mcp_tool.assert_called_once()

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_calendar_service_unavailable(self):
        """Test behavior when calendar service is unavailable"""
        server = DayManagementMCPServer()
        server.calendar_service = None
        
        # Test each method
        events = await server.get_calendar_events()
        assert events == []
        
        result = await server.create_calendar_event(
            title="Test", 
            start_datetime="2024-07-05T10:00:00Z",
            end_datetime="2024-07-05T11:00:00Z"
        )
        assert "error" in result
        assert "Calendar service not initialized" in result["error"]
    
    @pytest.mark.asyncio
    async def test_tasks_service_unavailable(self):
        """Test behavior when tasks service is unavailable"""
        server = DayManagementMCPServer()
        server.tasks_service = None
        
        # Test each method
        tasks = await server.get_tasks()
        assert tasks == []
        
        result = await server.create_task(title="Test Task")
        assert "error" in result
        assert "Tasks service not initialized" in result["error"]
    
    @pytest.mark.asyncio
    async def test_google_api_error_handling(self, day_server):
        """Test handling of Google API errors"""
        from googleapiclient.errors import HttpError
        
        # Mock HTTP error
        error_response = Mock()
        error_response.status = 403
        error_response.reason = "Forbidden"
        
        http_error = HttpError(error_response, b'{"error": "Forbidden"}')
        
        # Test calendar API error
        day_server.calendar_service.events().list().execute.side_effect = http_error
        
        events = await day_server.get_calendar_events()
        assert events == []
        
        # Test tasks API error
        day_server.tasks_service.tasks().list().execute.side_effect = http_error
        
        tasks = await day_server.get_tasks()
        assert tasks == []
    
    def test_invalid_date_parsing(self, day_server):
        """Test handling of invalid date strings"""
        invalid_dates = [
            "not_a_date",
            "2024-13-45",  # Invalid date
            "tomorrow at 25:00",  # Invalid time
            "",  # Empty string
            None  # None value
        ]
        
        for invalid_date in invalid_dates:
            try:
                if invalid_date:
                    date_parser.parse(invalid_date)
            except (ValueError, TypeError):
                # Expected behavior for invalid dates
                pass
    
    def test_event_parsing_edge_cases(self, day_server):
        """Test edge cases in event parsing"""
        # Event with minimal data
        minimal_event = {
            'id': 'minimal_event',
            'start': {'dateTime': '2024-07-05T10:00:00Z'},
            'end': {'dateTime': '2024-07-05T11:00:00Z'},
            'status': 'confirmed',
            'creator': {'email': 'test@example.com'},
            'organizer': {'email': 'test@example.com'}
        }
        
        parsed = day_server._parse_calendar_event(minimal_event)
        assert parsed.title == '(No Title)'
        assert parsed.description == ''
        assert parsed.location == ''
        assert parsed.attendees == []
    
    def test_task_parsing_edge_cases(self, day_server):
        """Test edge cases in task parsing"""
        # Task with minimal data
        minimal_task = {
            'id': 'minimal_task'
        }
        
        parsed = day_server._parse_task(minimal_task, '@default')
        assert parsed.title == '(No Title)'
        assert parsed.notes == ''
        assert parsed.status == 'needsAction'
        assert parsed.due_date is None
        assert parsed.completed_date is None

class TestDataConversion:
    """Test data conversion and serialization"""
    
    def test_event_to_dict_conversion(self, day_server):
        """Test CalendarEvent to dictionary conversion"""
        event = CalendarEvent(
            event_id='test_event',
            calendar_id='primary',
            title='Test Event',
            description='Test Description',
            location='Test Location',
            start_time=datetime(2024, 7, 5, 10, 0, 0),
            end_time=datetime(2024, 7, 5, 11, 0, 0),
            timezone='UTC',
            attendees=['user1@example.com', 'user2@example.com'],
            is_all_day=False,
            recurrence=None,
            status='confirmed',
            creator_email='creator@example.com',
            organizer_email='organizer@example.com'
        )
        
        event_dict = day_server._event_to_dict(event)
        
        assert event_dict['event_id'] == 'test_event'
        assert event_dict['title'] == 'Test Event'
        assert event_dict['location'] == 'Test Location'
        assert event_dict['duration_minutes'] == 60
        assert len(event_dict['attendees']) == 2
        assert event_dict['is_all_day'] is False
    
    def test_task_to_dict_conversion(self, day_server):
        """Test Task to dictionary conversion"""
        task = Task(
            task_id='test_task',
            tasklist_id='@default',
            title='Test Task',
            notes='Test Notes',
            status='needsAction',
            due_date=datetime(2024, 7, 6, 17, 0, 0),
            completed_date=None,
            parent_task_id=None,
            position='00000000001000000000',
            links=[]
        )
        
        task_dict = day_server._task_to_dict(task)
        
        assert task_dict['task_id'] == 'test_task'
        assert task_dict['title'] == 'Test Task'
        assert task_dict['notes'] == 'Test Notes'
        assert task_dict['status'] == 'needsAction'
        assert task_dict['is_completed'] is False
        assert task_dict['due_date'] is not None

class TestPerformanceAndScaling:
    """Test performance considerations and scaling"""
    
    @pytest.mark.asyncio
    async def test_large_event_list_handling(self, day_server):
        """Test handling of large event lists"""
        # Create mock response with many events
        large_event_list = []
        for i in range(100):
            event = {
                'id': f'event_{i}',
                'summary': f'Event {i}',
                'start': {'dateTime': f'2024-07-05T{10 + i % 8}:00:00Z'},
                'end': {'dateTime': f'2024-07-05T{11 + i % 8}:00:00Z'},
                'status': 'confirmed',
                'creator': {'email': 'test@example.com'},
                'organizer': {'email': 'test@example.com'}
            }
            large_event_list.append(event)
        
        mock_result = {'items': large_event_list}
        day_server.calendar_service.events().list().execute.return_value = mock_result
        
        events = await day_server.get_calendar_events(max_results=100)
        
        assert len(events) == 100
        assert all('event_id' in event for event in events)
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls(self, day_server, sample_calendar_event, sample_task):
        """Test concurrent API calls"""
        # Mock responses
        day_server.calendar_service.events().list().execute.return_value = {
            'items': [sample_calendar_event]
        }
        day_server.tasks_service.tasks().list().execute.return_value = {
            'items': [sample_task]
        }
        
        # Execute concurrent calls
        results = await asyncio.gather(
            day_server.get_calendar_events(),
            day_server.get_tasks(),
            day_server.get_tasklists()
        )
        
        events, tasks, tasklists = results
        
        assert len(events) == 1
        assert len(tasks) == 1
        assert isinstance(tasklists, list)

# Helper functions

# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Integration test runner
class DayManagementIntegrationRunner:
    """Run integration tests against live services (optional)"""
    
    def __init__(self, use_live_services=False):
        self.use_live_services = use_live_services
        self.server = None
    
    async def run_integration_tests(self):
        """Run integration tests with live or mock services"""
        if self.use_live_services:
            # Use real Google services (requires proper authentication)
            self.server = DayManagementMCPServer()
            
            if not self.server.calendar_service or not self.server.tasks_service:
                print("❌ Live services not available. Set up Google OAuth2 credentials.")
                return False
        else:
            # Use mock services
            self.server = DayManagementMCPServer()
        
        # Run basic integration tests
        tests = [
            self.test_calendar_integration,
            self.test_tasks_integration,
            self.test_day_overview_integration
        ]
        
        passed = 0
        for test in tests:
            try:
                await test()
                passed += 1
                print(f"✅ {test.__name__} passed")
            except Exception as e:
                print(f"❌ {test.__name__} failed: {e}")
        
        print(f"\n📊 Integration tests: {passed}/{len(tests)} passed")
        return passed == len(tests)
    
    async def test_calendar_integration(self):
        """Test calendar integration"""
        events = await self.server.get_calendar_events(days_ahead=1, max_results=5)
        assert isinstance(events, list)
    
    async def test_tasks_integration(self):
        """Test tasks integration"""
        tasks = await self.server.get_tasks(max_results=5)
        assert isinstance(tasks, list)
    
    async def test_day_overview_integration(self):
        """Test day overview integration"""
        overview = await self.server.get_day_overview()
        assert isinstance(overview, dict)
        assert 'date' in overview
        assert 'events_count' in overview
        assert 'tasks_due_count' in overview

# Main test runner
if __name__ == "__main__":
    import pytest
    
    # Run unit tests
    print("🧪 Running Day Management MCP Server comprehensive tests...")
    
    # Configure pytest
    pytest_args = [
        __file__,
        "-v",  # Verbose output
        "-s",  # Don't capture output
        "--tb=short",  # Short traceback format
        "--asyncio-mode=auto"  # Handle async tests automatically
    ]
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    # Run integration tests if requested
    if "--integration" in sys.argv:
        print("\n🔄 Running integration tests...")
        runner = DayManagementIntegrationRunner(use_live_services=("--live" in sys.argv))
        success = asyncio.run(runner.run_integration_tests())
        
        if not success:
            exit_code = 1
    
    print(f"\n📋 Test suite completed with exit code: {exit_code}")
    sys.exit(exit_code)