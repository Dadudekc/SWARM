def send_message(self, message: Message) -> bool:
    """Send a message to the specified agent using pyguiauto."""
    if not message.validate():
        return False

    try:
        # For agent messages, use pyguiauto to send to agent coordinates
        if message.to_agent.startswith("Agent-"):
            agent_id = message.to_agent
            if agent_id in self.agent_coordinates:
                coords = self.agent_coordinates[agent_id]
                # Use pyguiauto to send the message to the agent's UI coordinates
                # Example: pyguiauto.click(coords['message_x'], coords['message_y'])
                # Then send the message content
                # Example: pyguiauto.write(message.format_content())
                # For now, log the action
                logger.info(f"Sending message to {agent_id} via pyguiauto at coordinates {coords}")
                return True
            else:
                logger.error(f"Agent {agent_id} not found in coordinates")
                return False
        else:
            # For non-agent messages, log or handle as needed
            logger.info(f"Non-agent message: {message.format_content()}")
            return True
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False 