import json
import heapq


class NavGraph:
    def __init__(self, json_path, level_name="level1"):
        """
        Initialize with path to JSON file and optional level name
        Defaults to 'level1' for backward compatibility
        """
        self.vertices = {}
        self.edges = {}
        self.level_name = level_name
        self.load_graph(json_path)

    def load_graph(self, json_path):
        """Loads the navigation graph from a JSON file for the specified level"""
        with open(json_path, "r") as file:
            data = json.load(file)

            # Check if the specified level exists
            if self.level_name not in data["levels"]:
                available_levels = list(data["levels"].keys())
                raise ValueError(
                    f"Level '{self.level_name}' not found. "
                    f"Available levels: {available_levels}"
                )

            level = data["levels"][self.level_name]

            # Load vertices with optional properties
            for i, vertex in enumerate(level["vertices"]):
                # Handle both tuple and dict formats
                if isinstance(vertex, (list, tuple)):
                    x, y = vertex[:2]
                    properties = vertex[2] if len(vertex) > 2 else {}
                else:  # Assume dict format
                    x = vertex["x"]
                    y = vertex["y"]
                    properties = vertex.get("properties", {})

                self.vertices[i] = {
                    "x": x,
                    "y": y,
                    "name": properties.get("name", ""),
                    "is_charger": properties.get("is_charger", False),
                }

            # Initialize adjacency list
            self.edges = {v: [] for v in self.vertices}

            # Load lanes
            for lane in level["lanes"]:
                # Handle both tuple and dict formats
                if isinstance(lane, (list, tuple)):
                    start, end = lane[:2]
                    properties = lane[2] if len(lane) > 2 else {}
                else:  # Assume dict format
                    start = lane["start"]
                    end = lane["end"]
                    properties = lane.get("properties", {})

                speed_limit = properties.get("speed_limit", 1)

                # Add bidirectional edges
                self.edges[start].append((end, speed_limit))
                self.edges[end].append((start, speed_limit))

    # ... (keep all other existing methods unchanged)

    def switch_level(self, json_path, new_level_name):
        """Switch to a different level in the same JSON file"""
        self.level_name = new_level_name
        self.vertices = {}
        self.edges = {}
        self.load_graph(json_path)

    def get_vertices(self):
        """Returns all vertices."""
        return self.vertices

    def get_lanes(self):
        """Returns all lanes with speed limits."""
        return [
            {"start": start, "end": end, "speed_limit": speed}
            for start in self.edges
            for end, speed in self.edges[start]
        ]

    def get_speed_limit(self, start, end):
        """Retrieve the speed limit between two vertices using get_lanes()."""
        for lane in self.get_lanes():  # Use the function instead of self.lanes
            if (lane["start"] == start and lane["end"] == end) or (
                lane["start"] == end and lane["end"] == start
            ):
                return lane["speed_limit"]
        return None  # No direct connectio

    def get_shortest_path(self, start, destination):
        """Finds the shortest path using Dijkstra's algorithm."""
        priority_queue = [(0, start, [])]  # (cost, current_node, path)
        visited = set()

        while priority_queue:
            cost, current, path = heapq.heappop(priority_queue)

            if current in visited:
                continue
            visited.add(current)

            path = path + [current]

            if current == destination:
                return path  # Return the shortest path

            for neighbor, speed in self.edges.get(current, []):
                if neighbor not in visited:
                    heapq.heappush(priority_queue, (cost + 1, neighbor, path))

        return None  # No path found


# Example usage
if __name__ == "__main__":
    graph = NavGraph(
        "C:\\Users\\pssan\\OneDrive\\Desktop\\GOAT\\data\\nav_graph_1.json"
    )
    print("Vertices:", graph.get_vertices())
    print("Lanes:", graph.get_lanes())
    print("Shortest path (0 → 10):", graph.get_shortest_path(0, 10))
