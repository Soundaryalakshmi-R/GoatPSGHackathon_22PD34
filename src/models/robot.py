import logging
from datetime import datetime


class Robot:
    def __init__(self, robot_id, start_vertex):
        self.robot_id = robot_id
        self.current_position = start_vertex
        self.destination = None
        self.status = "Idle"
        self.path = []
        self.setup_logger()

    def setup_logger(self):
        """Configure individual robot logger"""
        self.logger = logging.getLogger(f"Robot.{self.robot_id}")
        handler = logging.FileHandler(f"robot_{self.robot_id}.log")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        self.logger.addHandler(handler)

    def assign_task(self, destination, path):
        """Assign task with logging"""
        self.destination = destination
        self.path = path
        self.status = "Moving"
        self.logger.info(
            f"Task assigned: {self.current_position} -> {destination} via {path}"
        )

    def move(self):
        """Move robot with position logging"""
        if not self.path:
            self.status = "Task Complete"
            self.logger.info(f"Task completed at {self.current_position}")
            return False

        prev_position = self.current_position
        self.current_position = self.path.pop(0)
        self.logger.info(f"Moved {prev_position} -> {self.current_position}")

        if not self.path:
            self.status = "Task Complete"
            self.logger.info(f"Task completed at {self.current_position}")
            return False

        return True

    def wait(self):
        """Log waiting events"""
        if self.status != "Waiting":
            self.logger.info(f"Waiting at {self.current_position}")
            self.status = "Waiting"

    def get_status(self):
        """Return current status snapshot for GUI"""
        return {
            "id": self.robot_id,
            "position": self.current_position,
            "status": self.status,
            "destination": self.destination,
            "path": self.path.copy(),
        }
