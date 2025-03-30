import heapq


def dijkstra(graph, start, destination):
    """Find the shortest path using Dijkstra's algorithm."""
    priority_queue = [(0, start, [])]  # (cost, current_node, path)
    visited = set()

    while priority_queue:
        cost, current, path = heapq.heappop(priority_queue)

        if current in visited:
            continue
        visited.add(current)

        path = path + [current]

        if current == destination:
            return path  # Return the path if we reached the destination

        for neighbor, speed in graph.get_neighbors(current):
            if neighbor not in visited:
                heapq.heappush(priority_queue, (cost + 1, neighbor, path))

    return None  # No path found
