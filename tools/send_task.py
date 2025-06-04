"""
Send a system optimization task to an agent.
"""

import logging
from dreamos.core.messaging.cell_phone import CellPhone
from dreamos.core.messaging.message import MessageMode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('send_task')

def send_optimization_task():
    """Send a system optimization task to Agent-1."""
    try:
        # Initialize cell phone
        phone = CellPhone()
        logger.info("Cell phone initialized")
        
        # Prepare task message
        task_message = """[TASK] System Optimization Assignment:

1. Analyze current system performance
2. Identify optimization opportunities
3. Prioritize critical improvements
4. Implement efficiency enhancements
5. Monitor system metrics
6. Report optimization results

Proceed with system optimization task."""

        # Send task message
        success = phone.send_message(
            from_agent="task_manager",
            to_agent="Agent-1",
            message=task_message,
            priority=3  # High priority task
        )
        
        if success:
            logger.info("Task message sent successfully")
            
            # Get status
            status = phone.get_status()
            logger.info(f"Cell phone status: {status}")
        else:
            logger.error("Failed to send task message")
            
    except Exception as e:
        logger.error(f"Error during task assignment: {e}")
    finally:
        # Cleanup
        phone.shutdown()
        logger.info("Task assignment completed")

if __name__ == "__main__":
    send_optimization_task() 