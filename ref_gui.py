import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time
from datetime import datetime
import random


class EnhancedFleetGUI:
    def __init__(self, master, fleet_manager, traffic_manager):
        self.master = master
        self.fleet_manager = fleet_manager
        self.traffic_manager = traffic_manager

        # Initialize current_mode before setting up UI
        self.current_mode = "spawn"  # Default mode

        self.setup_main_window()
        self.initialize_data_structures()
        self.create_ui_components()
        self.setup_event_handlers()
        self.draw_graph()
        self.start_update_cycles()

    def setup_main_window(self):
        self.master.title("Advanced Fleet Management System")
        self.master.geometry("1400x900")
        self.master.configure(bg="#f0f0f0")

        # Configure grid weights to make canvas expandable
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(0, weight=1)

    def initialize_data_structures(self):
        self.vertices = {}
        self.robots = {}  # {robot_id: canvas_object}
        self.robot_data = {}  # {robot_id: {"color": ..., "path_line": ...}}
        self.selected_robot = None
        self.occupancy_warnings = set()
        self.robot_colors = [
            "#FF5252",
            "#FF4081",
            "#E040FB",
            "#7C4DFF",
            "#536DFE",
            "#448AFF",
            "#40C4FF",
            "#18FFFF",
            "#64FFDA",
            "#69F0AE",
            "#B2FF59",
            "#EEFF41",
        ]

    def create_ui_components(self):
        # Control Panel
        self.control_frame = tk.LabelFrame(
            self.master, text="Control Panel", padx=10, pady=10
        )
        self.control_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        tk.Button(
            self.control_frame,
            text="Spawn Robot Mode",
            command=self.set_spawn_mode,
            bg="#4CAF50",
            fg="white",
        ).pack(fill=tk.X, pady=2)
        tk.Button(
            self.control_frame,
            text="Assign Task Mode",
            command=self.set_task_mode,
            bg="#2196F3",
            fg="white",
        ).pack(fill=tk.X, pady=2)
        tk.Button(
            self.control_frame,
            text="Start Movement",
            command=self.start_movement,
            bg="#FF9800",
            fg="white",
        ).pack(fill=tk.X, pady=2)
        tk.Button(
            self.control_frame,
            text="Reset Simulation",
            command=self.reset_simulation,
            bg="#F44336",
            fg="white",
        ).pack(fill=tk.X, pady=2)

        # Status Panel
        self.status_frame = tk.LabelFrame(self.control_frame, text="System Status")
        self.status_frame.pack(fill=tk.X, pady=5)

        self.robot_count_label = tk.Label(self.status_frame, text="Active Robots: 0")
        self.robot_count_label.pack(anchor="w")
        self.task_count_label = tk.Label(self.status_frame, text="Active Tasks: 0")
        self.task_count_label.pack(anchor="w")
        self.alert_label = tk.Label(self.status_frame, text="Alerts: None", fg="green")
        self.alert_label.pack(anchor="w")

        # Visualization Canvas - with explicit size and expandable
        self.canvas = tk.Canvas(
            self.master, bg="white", highlightthickness=1, width=1000, height=700
        )
        self.canvas.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Log Panel
        self.log_frame = tk.LabelFrame(self.master, text="Event Log", padx=10, pady=10)
        self.log_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            height=8,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state="disabled",
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def setup_event_handlers(self):
        self.canvas.bind("<Button-1>", self.handle_canvas_click)
        self.canvas.bind("<Motion>", self.show_vertex_info)
        self.canvas.bind("<MouseWheel>", self.zoom_graph)
        self.canvas.bind("<B1-Motion>", self.pan_graph)

    def draw_graph(self):
        self.canvas.delete("all")
        raw_vertices = self.fleet_manager.graph.get_vertices()

        if not raw_vertices:
            return

        # Get canvas dimensions after it's rendered
        self.master.update()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate normalization factors with proper scaling
        all_x = [v["x"] for v in raw_vertices.values()]
        all_y = [v["y"] for v in raw_vertices.values()]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        # Add 10% padding and calculate scale factors
        padding = 0.1
        x_range = max_x - min_x
        y_range = max_y - min_y

        # Handle case where all vertices have same coordinates
        if x_range == 0:
            x_range = 1
        if y_range == 0:
            y_range = 1

        scale_x = (canvas_width * (1 - 2 * padding)) / x_range
        scale_y = (canvas_height * (1 - 2 * padding)) / y_range
        scale = min(scale_x, scale_y)

        # Calculate offsets to center the graph
        offset_x = padding * canvas_width - min_x * scale
        offset_y = padding * canvas_height - min_y * scale

        # Draw lanes first (under vertices)
        for lane in self.fleet_manager.graph.get_lanes():
            start, end = lane["start"], lane["end"]
            if start in raw_vertices and end in raw_vertices:
                x1 = offset_x + raw_vertices[start]["x"] * scale
                y1 = offset_y + raw_vertices[start]["y"] * scale
                x2 = offset_x + raw_vertices[end]["x"] * scale
                y2 = offset_y + raw_vertices[end]["y"] * scale
                self.canvas.create_line(x1, y1, x2, y2, fill="#aaa", width=2)

        # Draw vertices with both names and indices
        for idx, vertex in raw_vertices.items():
            x = offset_x + vertex["x"] * scale
            y = offset_y + vertex["y"] * scale
            self.vertices[idx] = (x, y)

            # Vertex circle
            color = "green" if vertex.get("is_charger") else "red"
            self.canvas.create_oval(
                x - 12,
                y - 12,
                x + 12,
                y + 12,
                fill=color,
                outline="black",
                width=2,
                tags=f"vertex_{idx}",
            )

            # Display both name and index in stacked format
            name = vertex.get("name", "")
            display_text = f"{name}\n({idx})" if name else str(idx)

            self.canvas.create_text(
                x,
                y - 25,
                text=display_text,
                font=("Arial", 9, "bold"),
                fill="black",
                tags=f"label_{idx}",
            )

    def reset_simulation(self):
        """Properly reset both the fleet manager and GUI state"""
        # Clear fleet manager
        self.fleet_manager.robots.clear()

        # Clear GUI tracking
        for robot_id in list(self.robots.keys()):
            # Remove visual elements
            self.canvas.delete(self.robots[robot_id])
            self.canvas.delete(self.robot_data[robot_id]["label"])
            if self.robot_data[robot_id]["path_line"]:
                self.canvas.delete(self.robot_data[robot_id]["path_line"])

            # Remove from tracking dictionaries
            del self.robots[robot_id]
            del self.robot_data[robot_id]

        # Reset selection
        self.selected_robot = None
        self.current_mode = "spawn"

        # Reset counters in fleet manager if they exist
        if hasattr(self.fleet_manager, "robot_counter"):
            self.fleet_manager.robot_counter = 0

        self.log_event("Simulation completely reset")
        self.update_status_panel()

    def spawn_robot(self, vertex_id):
        """Modified spawn method to ensure proper ID synchronization"""
        if vertex_id not in self.vertices:
            self.log_event(f"Cannot spawn robot at invalid vertex {vertex_id}", "error")
            return

        # Generate ID that matches fleet manager's pattern
        robot_id = f"R{len(self.fleet_manager.robots) + 1}"

        # Spawn in fleet manager first
        self.fleet_manager.spawn_robot(vertex_id)

        # Only proceed if the robot was actually created
        if robot_id not in self.fleet_manager.robots:
            self.log_event(f"Failed to spawn robot {robot_id}", "error")
            return

        # Assign random color
        color = random.choice(self.robot_colors)
        x, y = self.vertices[vertex_id]

        # Create visual elements
        robot_circle = self.canvas.create_oval(
            x - 10, y - 10, x + 10, y + 10, fill=color, outline="black", width=2
        )
        robot_label = self.canvas.create_text(
            x, y + 20, text=robot_id, font=("Arial", 8, "bold")
        )

        # Store references
        self.robots[robot_id] = robot_circle
        self.robot_data[robot_id] = {
            "color": color,
            "label": robot_label,
            "path_line": None,
        }

        self.log_event(f"Robot {robot_id} spawned at vertex {vertex_id}")
        self.update_status_panel()

    def handle_canvas_click(self, event):
        """Safe click handler with error checking"""
        if not self.vertices:
            return

        # Find nearest vertex
        vertex_id = min(
            self.vertices.keys(),
            key=lambda v: (self.vertices[v][0] - event.x) ** 2
            + (self.vertices[v][1] - event.y) ** 2,
        )

        try:
            if self.current_mode == "spawn":
                self.spawn_robot(vertex_id)
            elif self.current_mode == "task":
                if self.selected_robot:
                    # Verify robot still exists
                    if self.selected_robot not in self.fleet_manager.robots:
                        self.log_event("Selected robot no longer exists", "error")
                        self.selected_robot = None
                        return

                    self.assign_task(self.selected_robot, vertex_id)
                    self.selected_robot = None
                else:
                    # Select a robot with existence check
                    for rid, rob in list(self.robots.items()):
                        if rid not in self.fleet_manager.robots:
                            continue

                        x, y = self.vertices[
                            self.fleet_manager.robots[rid].current_position
                        ]
                        if (x - event.x) ** 2 + (y - event.y) ** 2 <= 144:
                            self.selected_robot = rid
                            self.canvas.itemconfig(rob, outline="yellow", width=3)
                            self.log_event(f"Selected robot {rid} for task assignment")
                            break
        except Exception as e:
            self.log_event(f"Error handling click: {str(e)}", "error")

    def assign_task(self, robot_id, destination):
        if robot_id not in self.robots:
            self.log_event(f"Invalid robot selected: {robot_id}", "error")
            return

        path = self.fleet_manager.graph.get_shortest_path(
            self.fleet_manager.robots[robot_id].current_position, destination
        )

        if not path:
            self.log_event(f"No valid path to {destination} for {robot_id}", "warning")
            return

        # Visualize the path
        if self.robot_data[robot_id]["path_line"]:
            self.canvas.delete(self.robot_data[robot_id]["path_line"])

        path_points = [self.vertices[v] for v in path]
        path_line = self.canvas.create_line(
            *[coord for point in path_points for coord in point],
            fill=self.robot_data[robot_id]["color"],
            width=2,
            dash=(5, 2),
            arrow=tk.LAST,
        )
        self.robot_data[robot_id]["path_line"] = path_line

        self.fleet_manager.assign_task(robot_id, destination)
        self.log_event(f"Task assigned: {robot_id} → {destination} via {path}")

    def update_visuals(self):
        active_robots = 0
        active_tasks = 0

        for robot_id, robot_obj in self.robots.items():
            robot = self.fleet_manager.robots.get(robot_id)
            if not robot:
                continue

            x, y = self.vertices[robot.current_position]
            self.canvas.coords(robot_obj, x - 10, y - 10, x + 10, y + 10)
            self.canvas.coords(self.robot_data[robot_id]["label"], x, y + 20)

            # Update status color
            if robot.status == "Moving":
                color = self.robot_data[robot_id]["color"]
                active_robots += 1
                active_tasks += 1
            elif robot.status == "Waiting":
                color = "orange"
                active_robots += 1
                active_tasks += 1
            elif robot.status == "Charging":
                color = "green"
            else:  # Idle or Task Complete
                color = "gray"

            self.canvas.itemconfig(robot_obj, fill=color)

            # Update path visualization
            if robot.path and self.robot_data[robot_id]["path_line"]:
                path_points = [
                    self.vertices[v] for v in [robot.current_position] + robot.path
                ]
                self.canvas.coords(
                    self.robot_data[robot_id]["path_line"],
                    *[coord for point in path_points for coord in point],
                )

        self.robot_count_label.config(text=f"Active Robots: {active_robots}")
        self.task_count_label.config(text=f"Active Tasks: {active_tasks}")
        self.master.after(200, self.update_visuals)

    def log_event(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")

        if level == "error":
            self.alert_label.config(text=f"ALERT: {message[:50]}...", fg="red")
        elif level == "warning":
            self.alert_label.config(text=f"Warning: {message[:50]}...", fg="orange")
        else:
            self.alert_label.config(text="Status: Normal", fg="green")

        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def start_movement(self):
        def movement_thread():
            while True:
                active_robots = [
                    r
                    for r in self.fleet_manager.robots.values()
                    if r.status == "Moving" and r.path
                ]
                if not active_robots:
                    break

                for robot in active_robots:
                    next_pos = robot.path[0]
                    if self.traffic_manager.request_lane(
                        robot.robot_id, robot.current_position, next_pos
                    ):
                        robot.move()
                        self.traffic_manager.release_lane(
                            robot.current_position, next_pos
                        )
                        self.log_event(
                            f"{robot.robot_id} moved to {robot.current_position}"
                        )
                    else:
                        robot.wait()
                        self.log_event(
                            f"{robot.robot_id} waiting at {robot.current_position}"
                        )

                time.sleep(0.5)

        threading.Thread(target=movement_thread, daemon=True).start()

    def set_spawn_mode(self):
        self.current_mode = "spawn"
        self.log_event("Spawn mode activated - click on vertices to spawn robots")

    def set_task_mode(self):
        self.current_mode = "task"
        self.selected_robot = None
        self.log_event("Task mode activated - select a robot then destination")

    def update_status_panel(self):
        self.robot_count_label.config(
            text=f"Active Robots: {len(self.fleet_manager.robots)}"
        )
        self.task_count_label.config(
            text=f"Active Tasks: {sum(1 for r in self.fleet_manager.robots.values() if r.status == 'Moving')}"
        )

    def start_update_cycles(self):
        self.update_visuals()
        self.update_status_panel()
        self.master.after(1000, self.check_occupancy)

    def check_occupancy(self):
        # Check for traffic conflicts and update warnings
        self.master.after(1000, self.check_occupancy)

    def zoom_graph(self, event):
        # Zoom functionality
        pass

    def pan_graph(self, event):
        # Pan functionality
        pass

    def show_vertex_info(self, event):
        # Show tooltip with vertex info
        pass
