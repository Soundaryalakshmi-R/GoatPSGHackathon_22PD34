import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import time
from datetime import datetime
import random
import logging


class EnhancedFleetGUI:
    def __init__(self, master, fleet_manager, traffic_manager):
        self.master = master
        self.fleet_manager = fleet_manager
        self.traffic_manager = traffic_manager

        # Initialize current_mode before setting up UI
        self.current_mode = "spawn"  # Default mode
        self.setup_logging()
        self.movement_trails = {}

        self.setup_main_window()
        self.initialize_data_structures()
        self.create_ui_components()
        self.setup_event_handlers()
        self.draw_graph()
        self.start_update_cycles()

        self.STATUS_COLORS = {
            "Idle": "gray",
            "Moving": "green",
            "Waiting": "orange",
            "Charging": "blue",
            "Task Complete": "purple",
            "Task Complete": "#9C27B0",
        }

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

        self.robot_icons = {
            "default": "●",
            "charging": "⚡",
            "waiting": "◼",
            "moving": "➤",
        }

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

        self.master.update()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        all_x = [v["x"] for v in raw_vertices.values()]
        all_y = [v["y"] for v in raw_vertices.values()]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        padding = 0.1
        x_range = max_x - min_x or 1
        y_range = max_y - min_y or 1

        scale_x = (canvas_width * (1 - 2 * padding)) / x_range
        scale_y = (canvas_height * (1 - 2 * padding)) / y_range
        scale = min(scale_x, scale_y)

        offset_x = padding * canvas_width - min_x * scale
        offset_y = padding * canvas_height - min_y * scale

        for lane in self.fleet_manager.graph.get_lanes():
            start, end = lane["start"], lane["end"]
            if start in raw_vertices and end in raw_vertices:
                x1, y1 = (
                    offset_x + raw_vertices[start]["x"] * scale,
                    offset_y + raw_vertices[start]["y"] * scale,
                )
                x2, y2 = (
                    offset_x + raw_vertices[end]["x"] * scale,
                    offset_y + raw_vertices[end]["y"] * scale,
                )
                self.canvas.create_line(x1, y1, x2, y2, fill="#aaa", width=2)

        for idx, vertex in raw_vertices.items():
            x, y = offset_x + vertex["x"] * scale, offset_y + vertex["y"] * scale
            self.vertices[idx] = (x, y)
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
            display_text = (
                f"{vertex.get('name', '')}\n({idx})" if vertex.get("name") else str(idx)
            )
            self.canvas.create_text(
                x,
                y - 25,
                text=display_text,
                font=("Arial", 9, "bold"),
                fill="black",
                tags=f"label_{idx}",
            )

    def reset_simulation(self):
        self.fleet_manager.robots.clear()
        if hasattr(self.traffic_manager, "occupied_lanes"):
            self.traffic_manager.occupied_lanes.clear()
        if hasattr(self.traffic_manager, "waiting_queues"):
            self.traffic_manager.waiting_queues.clear()
        if hasattr(self.traffic_manager, "lane_reservations"):
            self.traffic_manager.lane_reservations.clear()

        for robot_id in list(self.robots.keys()):
            self.canvas.delete(f"robot_{robot_id}")
            self.canvas.delete(f"status_{robot_id}")
            self.canvas.delete(f"label_{robot_id}")
            self.canvas.delete(f"path_{robot_id}")
            if "path_line" in self.robot_data.get(robot_id, {}):
                self.canvas.delete(self.robot_data[robot_id]["path_line"])

        self.robots.clear()
        self.robot_data.clear()
        self.selected_robot = None
        self.canvas.delete("queue_marker")
        self.canvas.delete("collision_marker")
        if hasattr(self.fleet_manager, "robot_counter"):
            self.fleet_manager.robot_counter = 0

        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        self.current_mode = "spawn"
        self.update_status_panel()
        self.log_event("Simulation completely reset")

    def spawn_robot(self, vertex_id):
        if vertex_id not in self.vertices:
            self.log_event(f"Cannot spawn robot at invalid vertex {vertex_id}", "error")
            return

        robot_id = f"R{len(self.fleet_manager.robots) + 1}"
        self.fleet_manager.spawn_robot(vertex_id)
        if robot_id not in self.fleet_manager.robots:
            self.log_event(f"Failed to spawn robot {robot_id}", "error")
            return

        x, y = self.vertices[vertex_id]
        color = self.robot_colors[len(self.robots) % len(self.robot_colors)]

        robot_body = self.canvas.create_oval(
            x - 12,
            y - 12,
            x + 12,
            y + 12,
            fill=color,
            outline="black",
            width=2,
            tags=f"robot_{robot_id}",
        )
        status_text = self.canvas.create_text(
            x + 25,
            y,
            text="Idle",
            font=("Arial", 8),
            anchor="w",
            tags=f"status_{robot_id}",
        )
        id_label = self.canvas.create_text(
            x,
            y + 25,
            text=robot_id,
            font=("Arial", 8, "bold"),
            tags=f"label_{robot_id}",
        )

        self.robots[robot_id] = robot_body
        self.robot_data[robot_id] = {
            "color": color,
            "status_text": status_text,
            "id_label": id_label,
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
        self.log_event(f"Task assigned: {robot_id} -> {destination} via {path}")

    def update_visuals(self):
        """Update positions and status text without changing colors"""
        for robot_id, robot in self.fleet_manager.robots.items():
            if robot_id not in self.robots:
                continue

            # Get current position
            x, y = self.vertices[robot.current_position]

            # Update positions
            self.canvas.coords(f"robot_{robot_id}", x - 12, y - 12, x + 12, y + 12)
            self.canvas.coords(f"status_{robot_id}", x + 25, y)
            self.canvas.coords(f"label_{robot_id}", x, y + 25)

            # Update status text only
            self.canvas.itemconfig(f"status_{robot_id}", text=robot.status)

            # Update icon if using them
            icon = self.robot_icons.get(
                robot.status.lower(), self.robot_icons["default"]
            )
            if f"icon_{robot_id}" in self.canvas.find_all():
                self.canvas.itemconfig(f"icon_{robot_id}", text=icon)

        self.master.after(100, self.update_visuals)

    def update_traffic_visuals(self):
        """Show waiting queues without affecting robot colors"""
        self.canvas.delete("queue_marker")
        for lane, queue in self.traffic_manager.waiting_queues.items():
            if queue:
                start, end = lane
                x1, y1 = self.vertices[start]
                x2, y2 = self.vertices[end]

                # Create dashed line for blocked lanes
                self.canvas.create_line(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill="red",
                    width=2,
                    dash=(4, 2),
                    tags="queue_marker",
                )

                # Add queue count
                self.canvas.create_text(
                    (x1 + x2) / 2,
                    (y1 + y2) / 2,
                    text=str(len(queue)),
                    fill="red",
                    font=("Arial", 8, "bold"),
                    tags="queue_marker",
                )

    def log_event(self, message, level="info"):
        """Log to both GUI and file with consistent timestamp format"""
        safe_message = message.replace("→", "->")
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {safe_message}"

        # Write to GUI
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, log_entry + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

        # Write to file
        if level == "error":
            self.system_log.error(f"[{timestamp}] {safe_message}")
        elif level == "warning":
            self.system_log.warning(f"[{timestamp}] {safe_message}")
        else:
            self.system_log.info(f"[{timestamp}] {safe_message}")

    def start_movement(self):
        """Movement coordination with both lane and collision management"""

        def movement_thread():
            while True:
                active_robots = [
                    r
                    for r in self.fleet_manager.robots.values()
                    if r.status in ("Moving", "Waiting") and r.path
                ]
                if not active_robots:
                    time.sleep(0.1)
                    continue

                for robot in active_robots:
                    if robot.move():
                        if robot.status == "Moving":
                            self.master.after(
                                0,
                                self.log_event,
                                f"{robot.robot_id} moved to {robot.current_position}",
                            )
                        else:
                            self.master.after(
                                0,
                                self.log_event,
                                f"{robot.robot_id} waiting at {robot.current_position}",
                            )
                    else:
                        self.master.after(
                            0,
                            self.log_event,
                            f"{robot.robot_id} completed task at {robot.current_position}",
                        )
                        self.master.after(
                            0,
                            lambda rid=robot.robot_id: self.canvas.delete(
                                self.robot_data[rid]["path_line"]
                            ),
                        )
                        self.master.after(
                            0,
                            lambda rid=robot.robot_id: self.robot_data[rid].update(
                                {"path_line": None}
                            ),
                        )

                self.master.after(0, self.update_visuals)
                time.sleep(0.5)

        threading.Thread(target=movement_thread, daemon=True).start()
        self.log_event("Movement system activated with collision prevention")

    def setup_logging(self):
        """Configure dual logging (GUI and file) with consistent timestamp format"""
        # Remove any existing handlers
        logging.getLogger().handlers = []

        # Create logger
        self.system_log = logging.getLogger("FleetGUI")
        self.system_log.setLevel(logging.INFO)

        # File handler for logs.txt
        file_handler = logging.FileHandler(
            "logs/fleet_logs.txt", mode="a", encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        # Add handlers
        self.system_log.addHandler(file_handler)

        # Don't propagate to root logger
        self.system_log.propagate = False

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
