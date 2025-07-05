#!/usr/bin/env python3
"""
Day Management MCP Server for Friday AI Assistant
Provides comprehensive day management through Google Calendar and Google Tasks APIs
"""

import os
import sys
import json
import time
import signal
import asyncio
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta, date
from dataclasses import dataclass
import logging
import pytz
from dateutil import parser as date_parser

# FastMCP imports
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: FastMCP not installed. Install with: pip install fastmcp")
    sys.exit(1)

# Google API imports
try:
    import pickle
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"Warning: Google API libraries import failed: {e}")
    print("Install with: pip install google-api-python-client google-auth google-auth-oauthlib")
    sys.exit(1)

# Environment variables
from dotenv import load_dotenv
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('day_management_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Google API scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks'
]

@dataclass
class CalendarEvent:
    """Represents a calendar event"""
    event_id: str
    calendar_id: str
    title: str
    description: str
    location: str
    start_time: datetime
    end_time: datetime
    timezone: str
    attendees: List[str]
    is_all_day: bool
    recurrence: Optional[List[str]]
    status: str
    creator_email: str
    organizer_email: str

@dataclass
class Task:
    """Represents a task/todo item"""
    task_id: str
    tasklist_id: str
    title: str
    notes: str
    status: str
    due_date: Optional[datetime]
    completed_date: Optional[datetime]
    parent_task_id: Optional[str]
    position: str
    links: List[Dict]

class DayManagementMCPServer:
    """
    Day Management MCP Server for Friday AI Assistant
    Handles Google Calendar and Google Tasks integration
    """
    
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "day_credentials.json")
        self.token_path = os.getenv("GOOGLE_TOKEN_PATH", "day_token.pickle")
        self.calendar_service = None
        self.tasks_service = None
        self.credentials = None
        self.timezone = pytz.timezone(os.getenv("USER_TIMEZONE", "UTC"))
        
        # Initialize Google API services
        try:
            self.calendar_service, self.tasks_service = self._get_google_services()
        except Exception as e:
            logger.error(f"Failed to initialize Google services: {e}")
            self.calendar_service = None
            self.tasks_service = None
    
    def _get_google_services(self):
        """Initialize Google Calendar and Tasks services with authentication"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, run OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Google credentials file not found: {self.credentials_path}\n"
                        "Please download from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        calendar_service = build('calendar', 'v3', credentials=creds)
        tasks_service = build('tasks', 'v1', credentials=creds)
        
        return calendar_service, tasks_service
    
    def _parse_calendar_event(self, event_data: Dict, calendar_id: str = 'primary') -> CalendarEvent:
        """Parse Google Calendar event data into CalendarEvent object"""
        try:
            # Handle different datetime formats
            start = event_data.get('start', {})
            end = event_data.get('end', {})
            
            # Check if all-day event
            is_all_day = 'date' in start
            
            if is_all_day:
                start_time = datetime.strptime(start['date'], '%Y-%m-%d')
                end_time = datetime.strptime(end['date'], '%Y-%m-%d')
                timezone_str = str(self.timezone)
            else:
                start_time = date_parser.parse(start.get('dateTime', ''))
                end_time = date_parser.parse(end.get('dateTime', ''))
                timezone_str = start.get('timeZone', str(self.timezone))
            
            # Extract attendees
            attendees = []
            for attendee in event_data.get('attendees', []):
                attendees.append(attendee.get('email', ''))
            
            return CalendarEvent(
                event_id=event_data['id'],
                calendar_id=calendar_id,
                title=event_data.get('summary', '(No Title)'),
                description=event_data.get('description', ''),
                location=event_data.get('location', ''),
                start_time=start_time,
                end_time=end_time,
                timezone=timezone_str,
                attendees=attendees,
                is_all_day=is_all_day,
                recurrence=event_data.get('recurrence'),
                status=event_data.get('status', 'confirmed'),
                creator_email=event_data.get('creator', {}).get('email', ''),
                organizer_email=event_data.get('organizer', {}).get('email', '')
            )
            
        except Exception as e:
            logger.error(f"Error parsing calendar event: {e}")
            raise
    
    def _parse_task(self, task_data: Dict, tasklist_id: str) -> Task:
        """Parse Google Tasks data into Task object"""
        try:
            # Parse due date
            due_date = None
            if 'due' in task_data:
                due_date = date_parser.parse(task_data['due'])
            
            # Parse completed date
            completed_date = None
            if 'completed' in task_data:
                completed_date = date_parser.parse(task_data['completed'])
            
            # Parse links
            links = task_data.get('links', [])
            
            return Task(
                task_id=task_data['id'],
                tasklist_id=tasklist_id,
                title=task_data.get('title', '(No Title)'),
                notes=task_data.get('notes', ''),
                status=task_data.get('status', 'needsAction'),
                due_date=due_date,
                completed_date=completed_date,
                parent_task_id=task_data.get('parent'),
                position=task_data.get('position', ''),
                links=links
            )
            
        except Exception as e:
            logger.error(f"Error parsing task: {e}")
            raise
    
    async def get_calendar_events(self, 
                                 days_ahead: int = 7,
                                 calendar_id: str = 'primary',
                                 max_results: int = 50) -> List[Dict]:
        """
        Get calendar events for the next N days
        
        Args:
            days_ahead: Number of days to look ahead
            calendar_id: Calendar ID to query
            max_results: Maximum number of events
        
        Returns:
            List of event dictionaries
        """
        try:
            if not self.calendar_service:
                return []
            
            # Calculate time range
            now = datetime.utcnow()
            end_time = now + timedelta(days=days_ahead)
            
            # Get events
            events_result = self.calendar_service.events().list(
                calendarId=calendar_id,
                timeMin=now.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Parse events
            event_list = []
            for event in events:
                try:
                    event_obj = self._parse_calendar_event(event, calendar_id)
                    event_list.append(self._event_to_dict(event_obj))
                except Exception as e:
                    logger.error(f"Error processing event {event.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(event_list)} calendar events")
            return event_list
            
        except Exception as e:
            logger.error(f"Error retrieving calendar events: {e}")
            return []
    
    async def create_calendar_event(self,
                                   title: str,
                                   start_datetime: str,
                                   end_datetime: str,
                                   description: str = "",
                                   location: str = "",
                                   attendees: List[str] = None,
                                   calendar_id: str = 'primary') -> Dict:
        """
        Create a new calendar event
        
        Args:
            title: Event title
            start_datetime: Start time (ISO format or natural language)
            end_datetime: End time (ISO format or natural language)
            description: Event description
            location: Event location
            attendees: List of attendee emails
            calendar_id: Calendar to create event in
        
        Returns:
            Creation result dictionary
        """
        try:
            if not self.calendar_service:
                return {"error": "Calendar service not initialized"}
            
            # Parse datetime strings
            try:
                start_dt = date_parser.parse(start_datetime)
                end_dt = date_parser.parse(end_datetime)
            except Exception as e:
                return {"error": f"Invalid datetime format: {e}"}
            
            # Build event data
            event_data = {
                'summary': title,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': str(self.timezone),
                },
            }
            
            # Add attendees if provided
            if attendees:
                event_data['attendees'] = [{'email': email} for email in attendees]
            
            # Create event
            event = self.calendar_service.events().insert(
                calendarId=calendar_id,
                body=event_data
            ).execute()
            
            logger.info(f"Created calendar event: {title}")
            return {
                "success": True,
                "event_id": event['id'],
                "title": title,
                "start_time": start_dt.isoformat(),
                "calendar_link": event.get('htmlLink', '')
            }
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {"error": f"Failed to create event: {str(e)}"}
    
    async def update_calendar_event(self,
                                   event_id: str,
                                   title: str = None,
                                   start_datetime: str = None,
                                   end_datetime: str = None,
                                   description: str = None,
                                   location: str = None,
                                   calendar_id: str = 'primary') -> Dict:
        """
        Update an existing calendar event
        
        Args:
            event_id: Event ID to update
            title: New event title (optional)
            start_datetime: New start time (optional)
            end_datetime: New end time (optional)
            description: New description (optional)
            location: New location (optional)
            calendar_id: Calendar containing the event
        
        Returns:
            Update result dictionary
        """
        try:
            if not self.calendar_service:
                return {"error": "Calendar service not initialized"}
            
            # Get existing event
            event = self.calendar_service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields if provided
            if title is not None:
                event['summary'] = title
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            
            if start_datetime is not None:
                start_dt = date_parser.parse(start_datetime)
                event['start'] = {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': str(self.timezone),
                }
            
            if end_datetime is not None:
                end_dt = date_parser.parse(end_datetime)
                event['end'] = {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': str(self.timezone),
                }
            
            # Update event
            updated_event = self.calendar_service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info(f"Updated calendar event: {event_id}")
            return {
                "success": True,
                "event_id": event_id,
                "title": updated_event.get('summary', ''),
                "calendar_link": updated_event.get('htmlLink', '')
            }
            
        except Exception as e:
            logger.error(f"Error updating calendar event: {e}")
            return {"error": f"Failed to update event: {str(e)}"}
    
    async def delete_calendar_event(self,
                                   event_id: str,
                                   calendar_id: str = 'primary') -> Dict:
        """
        Delete a calendar event
        
        Args:
            event_id: Event ID to delete
            calendar_id: Calendar containing the event
        
        Returns:
            Deletion result dictionary
        """
        try:
            if not self.calendar_service:
                return {"error": "Calendar service not initialized"}
            
            # Delete event
            self.calendar_service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Deleted calendar event: {event_id}")
            return {
                "success": True,
                "event_id": event_id,
                "message": "Event deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting calendar event: {e}")
            return {"error": f"Failed to delete event: {str(e)}"}
    
    async def get_tasks(self,
                       tasklist_id: str = '@default',
                       max_results: int = 100,
                       show_completed: bool = True) -> List[Dict]:
        """
        Get tasks from a task list
        
        Args:
            tasklist_id: Task list ID (@default for default list)
            max_results: Maximum number of tasks
            show_completed: Include completed tasks
        
        Returns:
            List of task dictionaries
        """
        try:
            if not self.tasks_service:
                return []
            
            # Get tasks
            tasks_result = self.tasks_service.tasks().list(
                tasklist=tasklist_id,
                maxResults=max_results,
                showCompleted=show_completed,
                showHidden=True
            ).execute()
            
            tasks = tasks_result.get('items', [])
            
            # Parse tasks
            task_list = []
            for task in tasks:
                try:
                    task_obj = self._parse_task(task, tasklist_id)
                    task_list.append(self._task_to_dict(task_obj))
                except Exception as e:
                    logger.error(f"Error processing task {task.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(task_list)} tasks")
            return task_list
            
        except Exception as e:
            logger.error(f"Error retrieving tasks: {e}")
            return []
    
    async def create_task(self,
                         title: str,
                         notes: str = "",
                         due_date: str = None,
                         tasklist_id: str = '@default') -> Dict:
        """
        Create a new task
        
        Args:
            title: Task title
            notes: Task notes/description
            due_date: Due date (ISO format or natural language)
            tasklist_id: Task list to create task in
        
        Returns:
            Creation result dictionary
        """
        try:
            if not self.tasks_service:
                return {"error": "Tasks service not initialized"}
            
            # Build task data
            task_data = {
                'title': title,
                'notes': notes
            }
            
            # Add due date if provided
            if due_date:
                try:
                    due_dt = date_parser.parse(due_date)
                    task_data['due'] = due_dt.isoformat()
                except Exception as e:
                    return {"error": f"Invalid due date format: {e}"}
            
            # Create task
            task = self.tasks_service.tasks().insert(
                tasklist=tasklist_id,
                body=task_data
            ).execute()
            
            logger.info(f"Created task: {title}")
            return {
                "success": True,
                "task_id": task['id'],
                "title": title,
                "tasklist_id": tasklist_id
            }
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {"error": f"Failed to create task: {str(e)}"}
    
    async def update_task(self,
                         task_id: str,
                         title: str = None,
                         notes: str = None,
                         due_date: str = None,
                         status: str = None,
                         tasklist_id: str = '@default') -> Dict:
        """
        Update an existing task
        
        Args:
            task_id: Task ID to update
            title: New task title (optional)
            notes: New task notes (optional)
            due_date: New due date (optional)
            status: New status ('needsAction' or 'completed')
            tasklist_id: Task list containing the task
        
        Returns:
            Update result dictionary
        """
        try:
            if not self.tasks_service:
                return {"error": "Tasks service not initialized"}
            
            # Get existing task
            task = self.tasks_service.tasks().get(
                tasklist=tasklist_id,
                task=task_id
            ).execute()
            
            # Update fields if provided
            if title is not None:
                task['title'] = title
            if notes is not None:
                task['notes'] = notes
            if status is not None:
                task['status'] = status
                if status == 'completed':
                    task['completed'] = datetime.utcnow().isoformat() + 'Z'
            
            if due_date is not None:
                try:
                    due_dt = date_parser.parse(due_date)
                    task['due'] = due_dt.isoformat()
                except Exception as e:
                    return {"error": f"Invalid due date format: {e}"}
            
            # Update task
            updated_task = self.tasks_service.tasks().update(
                tasklist=tasklist_id,
                task=task_id,
                body=task
            ).execute()
            
            logger.info(f"Updated task: {task_id}")
            return {
                "success": True,
                "task_id": task_id,
                "title": updated_task.get('title', ''),
                "status": updated_task.get('status', '')
            }
            
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return {"error": f"Failed to update task: {str(e)}"}
    
    async def complete_task(self,
                           task_id: str,
                           tasklist_id: str = '@default') -> Dict:
        """
        Mark a task as completed
        
        Args:
            task_id: Task ID to complete
            tasklist_id: Task list containing the task
        
        Returns:
            Completion result dictionary
        """
        return await self.update_task(
            task_id=task_id,
            status='completed',
            tasklist_id=tasklist_id
        )
    
    async def get_tasklists(self) -> List[Dict]:
        """
        Get all task lists
        
        Returns:
            List of task list dictionaries
        """
        try:
            if not self.tasks_service:
                return []
            
            tasklists_result = self.tasks_service.tasklists().list().execute()
            tasklists = tasklists_result.get('items', [])
            
            result = []
            for tasklist in tasklists:
                result.append({
                    'id': tasklist['id'],
                    'title': tasklist['title'],
                    'updated': tasklist.get('updated', '')
                })
            
            logger.info(f"Retrieved {len(result)} task lists")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving task lists: {e}")
            return []
    
    async def get_day_overview(self, target_date: str = None) -> Dict:
        """
        Get a comprehensive overview of a specific day
        
        Args:
            target_date: Date to get overview for (default: today)
        
        Returns:
            Day overview dictionary
        """
        try:
            # Parse target date
            if target_date:
                target_dt = date_parser.parse(target_date).date()
            else:
                target_dt = date.today()
            
            # Get events for the day
            start_datetime = datetime.combine(target_dt, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            
            events_result = self.calendar_service.events().list(
                calendarId='primary',
                timeMin=start_datetime.isoformat() + 'Z',
                timeMax=end_datetime.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                event_obj = self._parse_calendar_event(event)
                events.append(self._event_to_dict(event_obj))
            
            # Get tasks due on this day
            tasks = await self.get_tasks(show_completed=False)
            due_tasks = []
            for task in tasks:
                if task['due_date']:
                    task_due = date_parser.parse(task['due_date']).date()
                    if task_due == target_dt:
                        due_tasks.append(task)
            
            return {
                "date": target_dt.isoformat(),
                "day_name": target_dt.strftime("%A"),
                "events_count": len(events),
                "events": events,
                "tasks_due_count": len(due_tasks),
                "tasks_due": due_tasks,
                "free_time_slots": self._calculate_free_time(events, target_dt)
            }
            
        except Exception as e:
            logger.error(f"Error getting day overview: {e}")
            return {"error": str(e)}
    
    def _calculate_free_time(self, events: List[Dict], target_date: date) -> List[Dict]:
        """Calculate free time slots between events"""
        try:
            # Working hours (9 AM to 6 PM)
            day_start = datetime.combine(target_date, datetime.min.time().replace(hour=9))
            day_end = datetime.combine(target_date, datetime.min.time().replace(hour=18))
            
            # Sort events by start time
            sorted_events = sorted(events, key=lambda x: x['start_time'])
            
            free_slots = []
            current_time = day_start
            
            for event in sorted_events:
                event_start = date_parser.parse(event['start_time'])
                
                # If there's a gap before this event
                if current_time < event_start:
                    free_slots.append({
                        "start": current_time.isoformat(),
                        "end": event_start.isoformat(),
                        "duration_minutes": int((event_start - current_time).total_seconds() / 60)
                    })
                
                # Update current time to end of this event
                event_end = date_parser.parse(event['end_time'])
                current_time = max(current_time, event_end)
            
            # Check for free time after last event
            if current_time < day_end:
                free_slots.append({
                    "start": current_time.isoformat(),
                    "end": day_end.isoformat(),
                    "duration_minutes": int((day_end - current_time).total_seconds() / 60)
                })
            
            return free_slots
            
        except Exception as e:
            logger.error(f"Error calculating free time: {e}")
            return []
    
    def _event_to_dict(self, event: CalendarEvent) -> Dict:
        """Convert CalendarEvent object to dictionary"""
        return {
            "event_id": event.event_id,
            "calendar_id": event.calendar_id,
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "timezone": event.timezone,
            "attendees": event.attendees,
            "is_all_day": event.is_all_day,
            "status": event.status,
            "duration_minutes": int((event.end_time - event.start_time).total_seconds() / 60),
            "relative_start": self._get_relative_time(event.start_time)
        }
    
    def _task_to_dict(self, task: Task) -> Dict:
        """Convert Task object to dictionary"""
        return {
            "task_id": task.task_id,
            "tasklist_id": task.tasklist_id,
            "title": task.title,
            "notes": task.notes,
            "status": task.status,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "completed_date": task.completed_date.isoformat() if task.completed_date else None,
            "parent_task_id": task.parent_task_id,
            "is_completed": task.status == 'completed',
            "is_overdue": self._is_task_overdue(task),
            "relative_due": self._get_relative_time(task.due_date) if task.due_date else None
        }
    
    def _is_task_overdue(self, task: Task) -> bool:
        """Check if a task is overdue"""
        if not task.due_date or task.status == 'completed':
            return False
        return task.due_date < datetime.now()
    
    def _get_relative_time(self, timestamp: datetime) -> str:
        """Get human-readable relative time"""
        if not timestamp:
            return ""
        
        now = datetime.now()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=None)
        if now.tzinfo is None:
            now = now.replace(tzinfo=None)
        
        diff = timestamp - now
        
        if diff.days > 0:
            return f"in {diff.days} day{'s' if diff.days != 1 else ''}"
        elif diff.days < 0:
            return f"{abs(diff.days)} day{'s' if abs(diff.days) != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"in {hours} hour{'s' if hours != 1 else ''}"
        elif diff.seconds < -3600:
            hours = abs(diff.seconds) // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            return "Today"

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print("\nShutting down Day Management MCP server...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Initialize FastMCP server
mcp = FastMCP(
    name="day-management-mcp",
    host="127.0.0.1",
    port=5003,
    timeout=30
)

# Initialize Day Management server
day_server = DayManagementMCPServer()

@mcp.tool()
async def get_calendar_events(days_ahead: int = 7,
                             max_results: int = 20) -> str:
    """
    Get upcoming calendar events.
    
    Parameters:
    - days_ahead: Number of days to look ahead (default: 7)
    - max_results: Maximum number of events (default: 20)
    
    Returns:
    - Formatted string with upcoming events
    """
    try:
        events = await day_server.get_calendar_events(days_ahead, 'primary', max_results)
        
        if not events:
            return f"No calendar events found for the next {days_ahead} days."
        
        # Format events for display
        formatted_events = []
        formatted_events.append(f"📅 UPCOMING CALENDAR EVENTS (next {days_ahead} days)")
        formatted_events.append("=" * 60)
        
        current_date = None
        for event in events:
            event_date = date_parser.parse(event['start_time']).date()
            
            # Add date header if new day
            if current_date != event_date:
                current_date = event_date
                formatted_events.append(f"\n📆 {event_date.strftime('%A, %B %d, %Y')}")
                formatted_events.append("-" * 40)
            
            # Format event
            start_time = date_parser.parse(event['start_time'])
            end_time = date_parser.parse(event['end_time'])
            
            if event['is_all_day']:
                time_str = "All Day"
            else:
                time_str = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
            
            formatted_events.append(f"\n🕐 {time_str}")
            formatted_events.append(f"📝 {event['title']}")
            
            if event['location']:
                formatted_events.append(f"📍 {event['location']}")
            
            if event['attendees']:
                formatted_events.append(f"👥 Attendees: {', '.join(event['attendees'][:3])}" + 
                                      (f" (+{len(event['attendees'])-3} more)" if len(event['attendees']) > 3 else ""))
            
            formatted_events.append(f"🆔 Event ID: {event['event_id']}")
        
        formatted_events.append(f"\n📊 Total events: {len(events)}")
        
        return "\n".join(formatted_events)
        
    except Exception as e:
        return f"Error retrieving calendar events: {str(e)}"

@mcp.tool()
async def create_calendar_event(title: str,
                               start_datetime: str,
                               end_datetime: str,
                               description: str = "",
                               location: str = "",
                               attendees: str = "") -> str:
    """
    Create a new calendar event.
    
    Parameters:
    - title: Event title (required)
    - start_datetime: Start time in ISO format or natural language (required)
    - end_datetime: End time in ISO format or natural language (required)
    - description: Event description (optional)
    - location: Event location (optional)
    - attendees: Comma-separated list of attendee emails (optional)
    
    Returns:
    - Result of the creation operation
    """
    try:
        # Parse attendees
        attendee_list = []
        if attendees:
            attendee_list = [email.strip() for email in attendees.split(',')]
        
        result = await day_server.create_calendar_event(
            title=title,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            location=location,
            attendees=attendee_list
        )
        
        if result.get("success"):
            return f"✅ Calendar event '{result['title']}' created successfully!\n🆔 Event ID: {result['event_id']}\n🕐 Start: {result['start_time']}\n🔗 Link: {result.get('calendar_link', 'N/A')}"
        else:
            return f"❌ Failed to create calendar event: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error creating calendar event: {str(e)}"

@mcp.tool()
async def update_calendar_event(event_id: str,
                               title: str = None,
                               start_datetime: str = None,
                               end_datetime: str = None,
                               description: str = None,
                               location: str = None) -> str:
    """
    Update an existing calendar event.
    
    Parameters:
    - event_id: Event ID to update (required)
    - title: New event title (optional)
    - start_datetime: New start time (optional)
    - end_datetime: New end time (optional)
    - description: New description (optional)
    - location: New location (optional)
    
    Returns:
    - Result of the update operation
    """
    try:
        result = await day_server.update_calendar_event(
            event_id=event_id,
            title=title,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            description=description,
            location=location
        )
        
        if result.get("success"):
            return f"✅ Calendar event updated successfully!\n🆔 Event ID: {result['event_id']}\n📝 Title: {result['title']}\n🔗 Link: {result.get('calendar_link', 'N/A')}"
        else:
            return f"❌ Failed to update calendar event: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error updating calendar event: {str(e)}"

@mcp.tool()
async def delete_calendar_event(event_id: str) -> str:
    """
    Delete a calendar event.
    
    Parameters:
    - event_id: Event ID to delete (required)
    
    Returns:
    - Result of the deletion operation
    """
    try:
        result = await day_server.delete_calendar_event(event_id)
        
        if result.get("success"):
            return f"✅ Calendar event deleted successfully!\n🆔 Event ID: {result['event_id']}"
        else:
            return f"❌ Failed to delete calendar event: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error deleting calendar event: {str(e)}"

@mcp.tool()
async def get_tasks(tasklist_id: str = "@default",
                   show_completed: bool = False,
                   max_results: int = 50) -> str:
    """
    Get tasks from a task list.
    
    Parameters:
    - tasklist_id: Task list ID (default: "@default")
    - show_completed: Include completed tasks (default: False)
    - max_results: Maximum number of tasks (default: 50)
    
    Returns:
    - Formatted string with tasks
    """
    try:
        tasks = await day_server.get_tasks(tasklist_id, max_results, show_completed)
        
        if not tasks:
            return f"No tasks found in the specified task list."
        
        # Separate completed and pending tasks
        pending_tasks = [t for t in tasks if not t['is_completed']]
        completed_tasks = [t for t in tasks if t['is_completed']]
        overdue_tasks = [t for t in pending_tasks if t['is_overdue']]
        
        # Format tasks for display
        formatted_tasks = []
        formatted_tasks.append(f"📋 TASKS OVERVIEW")
        formatted_tasks.append("=" * 50)
        formatted_tasks.append(f"📊 Total: {len(tasks)} | Pending: {len(pending_tasks)} | Completed: {len(completed_tasks)} | Overdue: {len(overdue_tasks)}")
        
        # Show overdue tasks first
        if overdue_tasks:
            formatted_tasks.append(f"\n🚨 OVERDUE TASKS ({len(overdue_tasks)})")
            formatted_tasks.append("-" * 30)
            for task in overdue_tasks:
                formatted_tasks.append(f"\n❗ {task['title']}")
                if task['due_date']:
                    formatted_tasks.append(f"📅 Due: {task['relative_due']}")
                if task['notes']:
                    formatted_tasks.append(f"📝 {task['notes'][:100]}...")
                formatted_tasks.append(f"🆔 Task ID: {task['task_id']}")
        
        # Show pending tasks
        if pending_tasks:
            formatted_tasks.append(f"\n📝 PENDING TASKS ({len(pending_tasks)})")
            formatted_tasks.append("-" * 30)
            for task in pending_tasks:
                if task in overdue_tasks:
                    continue  # Already shown in overdue section
                
                status_icon = "🔄" if task['status'] == 'needsAction' else "⏸️"
                formatted_tasks.append(f"\n{status_icon} {task['title']}")
                
                if task['due_date']:
                    formatted_tasks.append(f"📅 Due: {task['relative_due']}")
                if task['notes']:
                    formatted_tasks.append(f"📝 {task['notes'][:100]}...")
                formatted_tasks.append(f"🆔 Task ID: {task['task_id']}")
        
        # Show completed tasks if requested
        if show_completed and completed_tasks:
            formatted_tasks.append(f"\n✅ COMPLETED TASKS ({len(completed_tasks)})")
            formatted_tasks.append("-" * 30)
            for task in completed_tasks[:10]:  # Limit to 10 most recent
                formatted_tasks.append(f"\n✅ {task['title']}")
                if task['completed_date']:
                    completed_dt = date_parser.parse(task['completed_date'])
                    formatted_tasks.append(f"🎉 Completed: {completed_dt.strftime('%m/%d/%Y')}")
                formatted_tasks.append(f"🆔 Task ID: {task['task_id']}")
        
        return "\n".join(formatted_tasks)
        
    except Exception as e:
        return f"Error retrieving tasks: {str(e)}"

@mcp.tool()
async def create_task(title: str,
                     notes: str = "",
                     due_date: str = None,
                     tasklist_id: str = "@default") -> str:
    """
    Create a new task.
    
    Parameters:
    - title: Task title (required)
    - notes: Task notes/description (optional)
    - due_date: Due date in ISO format or natural language (optional)
    - tasklist_id: Task list to create task in (default: "@default")
    
    Returns:
    - Result of the creation operation
    """
    try:
        result = await day_server.create_task(
            title=title,
            notes=notes,
            due_date=due_date,
            tasklist_id=tasklist_id
        )
        
        if result.get("success"):
            return f"✅ Task '{result['title']}' created successfully!\n🆔 Task ID: {result['task_id']}\n📋 Task List: {result['tasklist_id']}"
        else:
            return f"❌ Failed to create task: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error creating task: {str(e)}"

@mcp.tool()
async def update_task(task_id: str,
                     title: str = None,
                     notes: str = None,
                     due_date: str = None,
                     status: str = None,
                     tasklist_id: str = "@default") -> str:
    """
    Update an existing task.
    
    Parameters:
    - task_id: Task ID to update (required)
    - title: New task title (optional)
    - notes: New task notes (optional)
    - due_date: New due date (optional)
    - status: New status ('needsAction' or 'completed') (optional)
    - tasklist_id: Task list containing the task (default: "@default")
    
    Returns:
    - Result of the update operation
    """
    try:
        result = await day_server.update_task(
            task_id=task_id,
            title=title,
            notes=notes,
            due_date=due_date,
            status=status,
            tasklist_id=tasklist_id
        )
        
        if result.get("success"):
            return f"✅ Task updated successfully!\n🆔 Task ID: {result['task_id']}\n📝 Title: {result['title']}\n📊 Status: {result['status']}"
        else:
            return f"❌ Failed to update task: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error updating task: {str(e)}"

@mcp.tool()
async def complete_task(task_id: str,
                       tasklist_id: str = "@default") -> str:
    """
    Mark a task as completed.
    
    Parameters:
    - task_id: Task ID to complete (required)
    - tasklist_id: Task list containing the task (default: "@default")
    
    Returns:
    - Result of the completion operation
    """
    try:
        result = await day_server.complete_task(task_id, tasklist_id)
        
        if result.get("success"):
            return f"✅ Task completed successfully!\n🆔 Task ID: {result['task_id']}\n🎉 Status: {result['status']}"
        else:
            return f"❌ Failed to complete task: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ Error completing task: {str(e)}"

@mcp.tool()
async def get_day_overview(target_date: str = None) -> str:
    """
    Get a comprehensive overview of a specific day.
    
    Parameters:
    - target_date: Date to get overview for (default: today)
    
    Returns:
    - Formatted day overview
    """
    try:
        overview = await day_server.get_day_overview(target_date)
        
        if "error" in overview:
            return f"Error getting day overview: {overview['error']}"
        
        # Format day overview
        formatted_overview = []
        formatted_overview.append(f"📅 DAY OVERVIEW - {overview['day_name']}, {overview['date']}")
        formatted_overview.append("=" * 60)
        
        # Events section
        formatted_overview.append(f"\n📆 CALENDAR EVENTS ({overview['events_count']})")
        formatted_overview.append("-" * 40)
        
        if overview['events']:
            for event in overview['events']:
                start_time = date_parser.parse(event['start_time'])
                end_time = date_parser.parse(event['end_time'])
                
                if event['is_all_day']:
                    time_str = "All Day"
                else:
                    time_str = f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"
                
                formatted_overview.append(f"\n🕐 {time_str} - {event['title']}")
                if event['location']:
                    formatted_overview.append(f"📍 {event['location']}")
        else:
            formatted_overview.append("No events scheduled")
        
        # Tasks section
        formatted_overview.append(f"\n📋 TASKS DUE ({overview['tasks_due_count']})")
        formatted_overview.append("-" * 40)
        
        if overview['tasks_due']:
            for task in overview['tasks_due']:
                status_icon = "❗" if task['is_overdue'] else "📝"
                formatted_overview.append(f"\n{status_icon} {task['title']}")
                if task['notes']:
                    formatted_overview.append(f"📝 {task['notes'][:50]}...")
        else:
            formatted_overview.append("No tasks due today")
        
        # Free time section
        formatted_overview.append(f"\n⏰ FREE TIME SLOTS")
        formatted_overview.append("-" * 40)
        
        if overview['free_time_slots']:
            for slot in overview['free_time_slots']:
                start_time = date_parser.parse(slot['start'])
                end_time = date_parser.parse(slot['end'])
                formatted_overview.append(f"\n🕐 {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')} ({slot['duration_minutes']} minutes)")
        else:
            formatted_overview.append("No significant free time slots available")
        
        return "\n".join(formatted_overview)
        
    except Exception as e:
        return f"Error getting day overview: {str(e)}"

@mcp.tool()
async def get_tasklists() -> str:
    """
    Get all available task lists.
    
    Returns:
    - Formatted string with task lists
    """
    try:
        tasklists = await day_server.get_tasklists()
        
        if not tasklists:
            return "No task lists found."
        
        # Format task lists
        formatted_lists = []
        formatted_lists.append("📋 AVAILABLE TASK LISTS")
        formatted_lists.append("=" * 40)
        
        for tasklist in tasklists:
            formatted_lists.append(f"\n📂 {tasklist['title']}")
            formatted_lists.append(f"🆔 ID: {tasklist['id']}")
            if tasklist['updated']:
                updated_dt = date_parser.parse(tasklist['updated'])
                formatted_lists.append(f"🔄 Updated: {updated_dt.strftime('%m/%d/%Y %I:%M %p')}")
        
        formatted_lists.append(f"\n📊 Total task lists: {len(tasklists)}")
        
        return "\n".join(formatted_lists)
        
    except Exception as e:
        return f"Error retrieving task lists: {str(e)}"

async def main():
    """Main function to run the MCP server"""
    try:
        print("Starting Day Management MCP server on 127.0.0.1:5003")
        
        # Check if Google services are available
        if day_server.calendar_service and day_server.tasks_service:
            print("Google Calendar and Tasks services initialized successfully")
        else:
            print("Warning: Google services not initialized - some features will be limited")
        
        # Start MCP server
        await mcp.run()
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())