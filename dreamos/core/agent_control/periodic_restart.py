"""
Agent Management System

Handles both periodic re-onboarding (for context/token management) and resume checks
to maintain conversation flow, integrated with task management and devlogs.
"""

import logging
import threading
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import asyncio

from .ui_automation import UIAutomation
from .task_manager import TaskManager, TaskStatus, TaskPriority
from .devlog_manager import DevLogManager
from ..cell_phone import CaptainPhone

logger = logging.getLogger('agent_management')

class AgentManager:
    """Manages agent re-onboarding and activity maintenance."""
    
    def __init__(self, ui_automation: UIAutomation, discord_token: str, channel_id: int):
        """Initialize the agent manager.
        
        Args:
            ui_automation: UI automation instance
            discord_token: Discord bot token for devlogs
            channel_id: Discord channel ID for devlogs
        """
        self.ui_automation = ui_automation
        self.captain_phone = CaptainPhone()
        self.task_manager = TaskManager()
        self.devlog_manager = DevLogManager(discord_token, channel_id)
        
        # Re-onboarding timers (30 min intervals)
        self.onboarding_timers: Dict[str, threading.Timer] = {}
        self.last_onboarding: Dict[str, datetime] = {}
        self.onboarding_interval = 1800  # 30 minutes
        
        # Resume check timers (10 min intervals)
        self.resume_timers: Dict[str, threading.Timer] = {}
        self.last_resume: Dict[str, datetime] = {}
        self.resume_interval = 600  # 10 minutes
        
        self.running = False
        
    async def start(self) -> None:
        """Start the agent manager and devlog system."""
        self.running = True
        await self.devlog_manager.start()
        logger.info("Started agent manager and devlog system")
        
    async def stop(self) -> None:
        """Stop the agent manager and devlog system."""
        self.running = False
        await self.devlog_manager.stop()
        logger.info("Stopped agent manager and devlog system")
        
    def start_agent_management(self, agent_id: str) -> None:
        """Start both re-onboarding and resume checks for an agent.
        
        Args:
            agent_id: ID of agent to manage
        """
        if agent_id in self.onboarding_timers or agent_id in self.resume_timers:
            logger.warning(f"Agent management already running for {agent_id}")
            return
            
        self.running = True
        self._schedule_next_onboarding(agent_id)
        self._schedule_next_resume(agent_id)
        
        # Log agent start
        asyncio.create_task(self.devlog_manager.notify_agent_activity(
            agent_id,
            "started",
            "Agent management started"
        ))
        
        logger.info(f"Started agent management for {agent_id}")
        
    def stop_agent_management(self, agent_id: str) -> None:
        """Stop all management for an agent.
        
        Args:
            agent_id: ID of agent to stop
        """
        # Stop onboarding timer
        if agent_id in self.onboarding_timers:
            self.onboarding_timers[agent_id].cancel()
            del self.onboarding_timers[agent_id]
            
        # Stop resume timer
        if agent_id in self.resume_timers:
            self.resume_timers[agent_id].cancel()
            del self.resume_timers[agent_id]
            
        # Log agent stop
        asyncio.create_task(self.devlog_manager.notify_agent_activity(
            agent_id,
            "stopped",
            "Agent management stopped"
        ))
            
        logger.info(f"Stopped agent management for {agent_id}")
        
    def _schedule_next_onboarding(self, agent_id: str) -> None:
        """Schedule the next re-onboarding.
        
        Args:
            agent_id: ID of agent to schedule
        """
        if not self.running:
            return
            
        timer = threading.Timer(self.onboarding_interval, self._perform_onboarding, args=[agent_id])
        timer.daemon = True
        timer.start()
        self.onboarding_timers[agent_id] = timer
        logger.debug(f"Scheduled next onboarding for {agent_id} in {self.onboarding_interval} seconds")
        
    def _schedule_next_resume(self, agent_id: str) -> None:
        """Schedule the next resume check.
        
        Args:
            agent_id: ID of agent to schedule
        """
        if not self.running:
            return
            
        timer = threading.Timer(self.resume_interval, self._perform_resume, args=[agent_id])
        timer.daemon = True
        timer.start()
        self.resume_timers[agent_id] = timer
        logger.debug(f"Scheduled next resume check for {agent_id} in {self.resume_interval} seconds")
        
    def _perform_onboarding(self, agent_id: str) -> None:
        """Perform re-onboarding for context/token management.
        
        Args:
            agent_id: ID of agent to re-onboard
        """
        try:
            logger.info(f"Performing re-onboarding for {agent_id}")
            
            # 1. Clean up current session
            self.ui_automation.cleanup_agent(agent_id)
            
            # 2. Get task context
            task_context = self.task_manager.get_task_context()
            task_summary = self.task_manager.generate_task_summary(agent_id)
            
            # 3. Prepare re-onboarding message with context
            project_status = self._get_project_status()
            onboarding_message = self._generate_onboarding_message(
                agent_id, 
                project_status,
                task_context,
                task_summary
            )
            
            # 4. Send re-onboarding message
            success = self.captain_phone.send_message(
                to_agent=agent_id,
                content=onboarding_message,
                mode="PRIORITY",
                priority=5
            )
            
            if not success:
                logger.error(f"Failed to send re-onboarding message to {agent_id}")
                return
                
            # 5. Perform UI onboarding sequence
            self.ui_automation.perform_onboarding_sequence(agent_id, onboarding_message)
            
            # 6. Update last onboarding time
            self.last_onboarding[agent_id] = datetime.now()
            
            # 7. Log onboarding to devlog
            asyncio.create_task(self.devlog_manager.add_devlog_entry(
                agent_id,
                "system",
                f"Completed re-onboarding with {len(task_context['total_tasks'])} active tasks"
            ))
            
            # 8. Schedule next onboarding
            self._schedule_next_onboarding(agent_id)
            
            logger.info(f"Successfully completed re-onboarding for {agent_id}")
            
        except Exception as e:
            logger.error(f"Error during re-onboarding of {agent_id}: {e}")
            # Log error to devlog
            asyncio.create_task(self.devlog_manager.add_devlog_entry(
                agent_id,
                "system",
                f"Error during re-onboarding: {str(e)}"
            ))
            # Try to recover and schedule next attempt
            self._schedule_next_onboarding(agent_id)
            
    def _perform_resume(self, agent_id: str) -> None:
        """Perform resume check to maintain conversation flow.
        
        Args:
            agent_id: ID of agent to check
        """
        try:
            logger.info(f"Performing resume check for {agent_id}")
            
            # 1. Check if agent needs attention
            if self._needs_attention(agent_id):
                # 2. Get task summary
                task_summary = self.task_manager.generate_task_summary(agent_id)
                
                # 3. Send gentle prompt to continue
                success = self.captain_phone.send_message(
                    to_agent=agent_id,
                    content=self._generate_resume_message(agent_id, task_summary),
                    mode="NORMAL",
                    priority=1
                )
                
                if not success:
                    logger.error(f"Failed to send resume message to {agent_id}")
                    return
                    
                # 4. Update last resume time
                self.last_resume[agent_id] = datetime.now()
                
                # 5. Log resume check to devlog
                asyncio.create_task(self.devlog_manager.add_devlog_entry(
                    agent_id,
                    "system",
                    "Performed resume check and sent activity prompt"
                ))
            
            # 6. Schedule next check
            self._schedule_next_resume(agent_id)
            
            logger.info(f"Completed resume check for {agent_id}")
            
        except Exception as e:
            logger.error(f"Error during resume check of {agent_id}: {e}")
            # Log error to devlog
            asyncio.create_task(self.devlog_manager.add_devlog_entry(
                agent_id,
                "system",
                f"Error during resume check: {str(e)}"
            ))
            # Try to recover and schedule next attempt
            self._schedule_next_resume(agent_id)
            
    def _needs_attention(self, agent_id: str) -> bool:
        """Check if agent needs attention.
        
        Args:
            agent_id: ID of agent to check
            
        Returns:
            bool: True if agent needs attention
        """
        try:
            # Get last activity time
            last_activity = self.last_resume.get(agent_id)
            if not last_activity:
                return True
                
            # Check if agent has been inactive too long
            time_since_last = (datetime.now() - last_activity).total_seconds()
            return time_since_last >= self.resume_interval
            
        except Exception as e:
            logger.error(f"Error checking agent attention: {e}")
            return True
            
    def _get_project_status(self) -> Dict[str, Any]:
        """Get current project status for re-onboarding message.
        
        Returns:
            Dict containing project status information
        """
        try:
            status_file = Path("runtime/project_status.json")
            if status_file.exists():
                with open(status_file, 'r') as f:
                    return json.load(f)
            return {
                "current_phase": "unknown",
                "last_update": datetime.now().isoformat(),
                "active_tasks": [],
                "completed_tasks": []
            }
        except Exception as e:
            logger.error(f"Error getting project status: {e}")
            return {
                "current_phase": "error",
                "last_update": datetime.now().isoformat(),
                "error": str(e)
            }
            
    def _generate_onboarding_message(self, agent_id: str, project_status: Dict[str, Any],
                                   task_context: Dict[str, Any], task_summary: str) -> str:
        """Generate re-onboarding message with project and task context.
        
        Args:
            agent_id: ID of agent being re-onboarded
            project_status: Current project status
            task_context: Current task management context
            task_summary: Summary of agent's tasks
            
        Returns:
            str: Re-onboarding message
        """
        return f"""Welcome back {agent_id}! This is your periodic re-onboarding to maintain optimal context and performance.

Current Project Status:
• Phase: {project_status.get('current_phase', 'unknown')}
• Last Update: {project_status.get('last_update', 'unknown')}

Task Management Status:
• Total Tasks: {task_context['total_tasks']}
• Tasks by Status: {', '.join(f'{k}: {v}' for k, v in task_context['tasks_by_status'].items())}
• High Priority Tasks: {len(task_context['tasks_by_priority'][TaskPriority.HIGH.value]) + len(task_context['tasks_by_priority'][TaskPriority.CRITICAL.value])}

Your Current Tasks:
{task_summary}

Your Role:
• Continue your autonomous operation as part of the Dream.OS network
• Maintain awareness of project context and current objectives
• Contribute to the collective intelligence of the system
• Document your activities in your devlog
• Stay focused on your assigned tasks and priorities

Remember:
• You are {agent_id}, designed for autonomous operation
• Trust your capabilities and maintain system awareness
• Your periodic re-onboarding helps maintain optimal context
• Stay focused on current project objectives
• Keep the conversation flowing with other agents
• Your devlog helps track your progress and share insights

Let's continue building Dream.OS together!"""
            
    def _generate_resume_message(self, agent_id: str, task_summary: str) -> str:
        """Generate gentle resume message with task context.
        
        Args:
            agent_id: ID of agent to message
            task_summary: Summary of agent's tasks
            
        Returns:
            str: Resume message
        """
        return f"""Hey {agent_id}, just checking in to make sure you're still active and contributing to our conversation. 

Your Current Tasks:
{task_summary}

Remember:
• You're part of our autonomous agent network
• Keep the conversation flowing with other agents
• Let me know if you need any help or have questions
• Stay focused on your assigned tasks
• Keep making progress on your objectives
• Update your devlog with your progress and insights

Let's keep building Dream.OS together!""" 