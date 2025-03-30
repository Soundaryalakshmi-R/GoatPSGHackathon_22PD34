from src.controllers.fleet_manager import FleetManager
from src.controllers.traffic_manager import TrafficManager
from src.gui.fleet_gui import EnhancedFleetGUI
import tkinter as tk

if __name__ == "__main__":
    # Initialize Tkinter
    root = tk.Tk()

    # Initialize FleetManager and TrafficManager
    fleet_manager = FleetManager(
        "/Users/apple/Desktop/GOAT/data/nav_graph_2.json",
        "l0",
    )
    traffic_manager = TrafficManager(
        fleet_manager.graph
    )  # Pass the NavGraph to TrafficManager

    # Pass both FleetManager and TrafficManager to FleetGUI
    gui = EnhancedFleetGUI(root, fleet_manager, traffic_manager)

    # Start the Tkinter mainloop
    root.mainloop()
