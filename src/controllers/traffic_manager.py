import time
import threading
from collections import defaultdict, deque
from threading import Lock


class TrafficManager:
    def __init__(self, graph):
        self.graph = graph
        self.occupied_lanes = set()  # Lanes currently in use {(start, end)}
        self.occupied_vertices = set()  # Occupied vertices
        self.waiting_queues = defaultdict(deque)  # {lane: deque(robot_ids)}
        self.vertex_locks = defaultdict(Lock)  # Locks for each vertex
        self.global_lock = Lock()  # High-level coordination

    def request_movement(self, robot_id, current_pos, next_pos):
        """Thread-safe movement request with queueing"""
        lane = (min(current_pos, next_pos), max(current_pos, next_pos))

        with self.vertex_locks[next_pos]:  # Use per-vertex lock for finer control
            if next_pos in self.occupied_vertices or lane in self.occupied_lanes:
                self.waiting_queues[lane].append(robot_id)
                return "waiting"

            # Reserve lane and target position
            self.occupied_lanes.add(lane)
            self.occupied_vertices.add(next_pos)
            return "approved"

    def complete_movement(self, robot_id, old_pos, new_pos):
        """Release resources and notify waiting robots"""
        lane = (min(old_pos, new_pos), max(old_pos, new_pos))

        with self.vertex_locks[old_pos]:  # Release previous position lock
            self.occupied_lanes.discard(lane)
            self.occupied_vertices.discard(old_pos)

        # Wake up the next waiting robot
        next_robot = None
        with self.global_lock:
            if self.waiting_queues[lane]:
                next_robot = self.waiting_queues[lane].popleft()

        return next_robot

    def manage_traffic(self, robots):
        """Continuously process waiting robots"""
        while True:
            time.sleep(0.1)  # Adjust for performance

            with self.global_lock:
                for lane in list(self.waiting_queues.keys()):
                    if not self.waiting_queues[lane]:
                        continue

                    start, end = lane
                    if (
                        end not in self.occupied_vertices
                        and lane not in self.occupied_lanes
                    ):
                        next_robot = self.waiting_queues[lane].popleft()
                        if (
                            next_robot in robots
                            and robots[next_robot].current_position == start
                        ):
                            self.occupied_lanes.add(lane)
                            self.occupied_vertices.add(end)
                            robots[next_robot].status = "approved"
