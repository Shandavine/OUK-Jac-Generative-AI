import os
from pathlib import Path
from typing import List, Dict
import random
import requests

# -----------------------------
# Directory Setup
# -----------------------------
SRC_DIR = Path("src_agri")
DOCS_DIR = Path("docs_agri")
DATA_DIR = Path("data_agri")

SRC_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# -----------------------------
# Graph Structures
# -----------------------------
class Node:
    def __init__(self, n_type: str, **props):
        self.n_type = n_type
        self.props = props
        self.id = id(self)

class Edge:
    def __init__(self, e_type: str, src: Node, dst: Node):
        self.e_type = e_type
        self.src = src
        self.dst = dst

class GraphSimple:
    def __init__(self):
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []

    def add_node(self, n_type: str, **props) -> Node:
        n = Node(n_type, **props)
        self.nodes.append(n)
        return n

    def add_edge(self, e_type: str, src: Node, dst: Node) -> Edge:
        e = Edge(e_type, src, dst)
        self.edges.append(e)
        return e

    def find_nodes(self, n_type: str) -> List[Node]:
        return [n for n in self.nodes if n.n_type == n_type]

# -----------------------------
# Smart Agriculture Logic
# -----------------------------
CROP_TEMPLATES = {
    "maize": {"ideal_temp": (20, 30), "ideal_moisture": (40, 70)},
    "tomato": {"ideal_temp": (18, 28), "ideal_moisture": (50, 80)},
    "tea": {"ideal_temp": (18, 25), "ideal_moisture": (60, 90)},
}

def fetch_weather(city: str) -> Dict:
    """Fetch current weather using a free API (replace with real API if available)"""
    # Simulated weather for demo
    return {
        "temperature": random.uniform(15, 35),
        "humidity": random.uniform(40, 90)
    }

def analyze_crop(field_name: str, crop: str, sensor_data: Dict) -> str:
    """Analyze crop data & provide advisory"""
    weather = fetch_weather(field_name)
    temp = sensor_data.get("temperature", weather["temperature"])
    moisture = sensor_data.get("soil_moisture", 50)
    humidity = sensor_data.get("humidity", weather["humidity"])

    advice = []
    crop_info = CROP_TEMPLATES.get(crop.lower(), {})

    min_temp, max_temp = crop_info.get("ideal_temp", (20, 30))
    min_moist, max_moist = crop_info.get("ideal_moisture", (40, 70))

    if moisture < min_moist:
        advice.append("Irrigate soon; soil moisture is low.")
    elif moisture > max_moist:
        advice.append("Reduce watering; soil is too wet.")

    if temp < min_temp:
        advice.append("Protect crops from cold.")
    elif temp > max_temp:
        advice.append("Consider shading; temperature is high.")

    if humidity > 85:
        advice.append("High humidity; check for fungal diseases.")

    if not advice:
        advice.append("Crops are healthy. Maintain current care.")

    return f"Field: {field_name}\nCrop: {crop}\nSoil Moisture: {moisture}\nTemp: {temp:.1f}°C\nHumidity: {humidity:.1f}%\n\nAdvice: {' '.join(advice)}"

# -----------------------------
# Main Execution
# -----------------------------
def main():
    g = GraphSimple()

    # Load or create sample field sensor data
    fields = ["Farm_A", "Farm_B"]
    crops = ["Maize", "Tomato", "Tea"]

    for field in fields:
        for crop in crops:
            file_path = DATA_DIR / f"{field}_{crop}.txt"
            if not file_path.exists():
                # Generate sample sensor data
                content = f"soil_moisture:{random.randint(20, 90)}\ntemperature:{random.randint(15, 35)}\nhumidity:{random.randint(40, 90)}"
                file_path.write_text(content)

            # Read sensor data
            content = file_path.read_text()
            data = {}
            for line in content.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    try:
                        data[k.strip()] = float(v.strip())
                    except ValueError:
                        data[k.strip()] = v.strip()

            # Create graph nodes
            file_node = g.add_node("sensor_file", path=str(file_path), content=content)
            advisory = analyze_crop(field, crop, data)
            doc_node = g.add_node("advisory", title=f"{field}_{crop} Advisory", body=advisory)
            g.add_edge("for_file", doc_node, file_node)

            # Save Markdown advisory
            out_file = DOCS_DIR / f"{field}_{crop}_advisory.md"
            out_file.write_text(f"# Advisory for {field} - {crop}\n\n{advisory}")
            print(f"Wrote {out_file}")

    print("✅ Smart Agriculture Advisory System docs generated successfully.")

if __name__ == "__main__":
    main()
