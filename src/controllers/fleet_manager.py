import time
from src.models.nav_graph import NavGraph
from src.models.robot import Robot


class FleetManager:
    def __init__(self, graph_file, levelname):
        self.graph = NavGraph(graph_file, levelname)
        self.robots = {}
        self.robot_counter = 0

    def spawn_robot(self, start_vertex):
        if start_vertex not in self.graph.vertices:
            print(f"❌ Invalid spawn location: {start_vertex}")
            return

        self.robot_counter += 1
        robot_id = f"R{self.robot_counter}"
        new_robot = Robot(robot_id, start_vertex)
        self.robots[robot_id] = new_robot
        print(f"✅ Robot {robot_id} spawned at {start_vertex}")

    def assign_task(self, robot_id, destination):
        if robot_id not in self.robots:
            print(f"❌ Robot {robot_id} not found")
            return

        if destination not in self.graph.vertices:
            print(f"❌ Invalid destination: {destination}")
            return

        robot = self.robots[robot_id]
        path = self.graph.get_shortest_path(robot.current_position, destination)

        if not path:
            print(f"⚠️ No valid path from {robot.current_position} to {destination}")
            return

        robot.assign_task(destination, path)  # 🔄 Fixed incorrect method call
        print(f"🚀 Robot {robot_id} assigned task to {destination} via {path}")

    def move_robots(self):
        while True:
            active_robots = [
                r for r in self.robots.values() if r.status != "Task Complete"
            ]
            if not active_robots:
                break

            for robot in active_robots:
                previous_position = robot.current_position
                robot.move()

                if robot.current_position != previous_position:
                    speed = self.graph.get_speed_limit(
                        previous_position, robot.current_position
                    )
                    print(
                        f"🤖 {robot.robot_id} moved to {robot.current_position} (Speed Limit: {speed})"
                    )

                time.sleep(1)  # ⏳ Simulate movement over time

        print("✅ All robots have reached their destinations.")
