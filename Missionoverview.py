import os
import xml.etree.ElementTree as ET
import json

def extract_game_data():
    card_map = {}
    item_map = {}
    missions = {}
    result_data = []

    # Global progression multiplier for gold rewards
    GOLD_MULTIPLIER = 7

    print("Starting extraction of XML structures...")

    # 1. Map card nomenclature (sections 1 to 21)
    for i in range(1, 22):
        filename = f"cards_section_{i}.xml"
        if not os.path.exists(filename):
            continue
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            for unit in root.findall('unit'):
                unit_id = unit.find('id')
                unit_name = unit.find('name')
                if unit_id is not None and unit_name is not None:
                    name_str = unit_name.text
                    card_map[unit_id.text] = name_str
                    
                    # Also map evolution / upgrade stages
                    for upgrade in unit.findall('upgrade'):
                        up_id = upgrade.find('card_id')
                        if up_id is not None:
                            card_map[up_id.text] = name_str
        except Exception as e:
            print(f"Notice regarding {filename}: {e}")

    # 2. Catalog items
    if os.path.exists("items.xml"):
        try:
            tree = ET.parse("items.xml")
            root = tree.getroot()
            for item in root.findall('item'):
                item_id = item.find('id')
                item_name = item.find('name')
                if item_id is not None and item_name is not None:
                    item_map[item_id.text] = item_name.text
        except Exception as e:
            print(f"Error parsing items.xml: {e}")

    # 3. Process missions and direct rewards
    if os.path.exists("missions.xml"):
        try:
            tree = ET.parse("missions.xml")
            root = tree.getroot()
            for mission in root.findall('mission'):
                m_id = mission.find('id').text if mission.find('id') is not None else ""
                m_name = mission.find('name').text if mission.find('name') is not None else ""
                energy = mission.find('energy').text if mission.find('energy') is not None else "0"
                
                missions[m_id] = {
                    "name": m_name,
                    "energy": int(energy) if energy.isdigit() else 0
                }
                
                # Extract direct mission rewards
                rewards_node = mission.find('rewards')
                if rewards_node is not None:
                    # Gold (with active global multiplier applied)
                    gold = rewards_node.find('gold')
                    if gold is not None and gold.text:
                        base_gold = int(gold.text) if gold.text.isdigit() else 0
                        multiplied_gold = base_gold * GOLD_MULTIPLIER
                        result_data.append({
                            "Mission ID": int(m_id) if m_id.isdigit() else m_id,
                            "Mission Name": m_name,
                            "Energy": int(energy) if energy.isdigit() else 0,
                            "Row Type": "Mission Reward",
                            "Level": 1,
                            "Reward Type": "Gold",
                            "Reward": f"{multiplied_gold} Gold",
                            "Achievement Name (may not match mission)": ""
                        })
                    # Card
                    card = rewards_node.find('card')
                    if card is not None and card.text:
                        c_id = card.text
                        result_data.append({
                            "Mission ID": int(m_id) if m_id.isdigit() else m_id,
                            "Mission Name": m_name,
                            "Energy": int(energy) if energy.isdigit() else 0,
                            "Row Type": "Mission Reward",
                            "Level": 1,
                            "Reward Type": "Card",
                            "Reward": card_map.get(c_id, f"Unknown Card ({c_id})"),
                            "Achievement Name (may not match mission)": ""
                        })
                    # Item
                    item = rewards_node.find('item')
                    if item is not None and item.text:
                        i_id = item.text
                        result_data.append({
                            "Mission ID": int(m_id) if m_id.isdigit() else m_id,
                            "Mission Name": m_name,
                            "Energy": int(energy) if energy.isdigit() else 0,
                            "Row Type": "Mission Reward",
                            "Level": 1,
                            "Reward Type": "Item",
                            "Reward": item_map.get(i_id, f"Unknown Item ({i_id})"),
                            "Achievement Name (may not match mission)": ""
                        })
        except Exception as e:
            print(f"Error parsing missions.xml: {e}")

    # 4. Link achievements associated with missions
    if os.path.exists("achievements.xml"):
        try:
            tree = ET.parse("achievements.xml")
            root = tree.getroot()
            for ach in root.findall('achievement'):
                ach_name = ach.find('name').text if ach.find('name') is not None else ""
                
                # Check if the achievement requires a mission
                req_node = ach.find('req')
                if req_node is not None:
                    m_id_node = req_node.find('mission')
                    if m_id_node is not None and m_id_node.text:
                        m_id = m_id_node.text
                        lvl_node = req_node.find('level')
                        lvl = int(lvl_node.text) if (lvl_node is not None and lvl_node.text and lvl_node.text.isdigit()) else 1
                        
                        m_info = missions.get(m_id, {"name": f"Campaign / Mission {m_id}", "energy": 0})
                        reward_node = ach.find('reward')
                        
                        if reward_node is not None:
                            # Card rewards inside achievements
                            for card in reward_node.findall('card'):
                                c_id = card.get('id') or card.text
                                amt = card.get('amount')
                                c_name = card_map.get(c_id, f"Unknown Card ({c_id})")
                                reward_str = f"{amt}x {c_name}" if amt else c_name
                                result_data.append({
                                    "Mission ID": int(m_id) if m_id.isdigit() else m_id,
                                    "Mission Name": m_info["name"],
                                    "Energy": m_info["energy"],
                                    "Row Type": "Achievement Reward",
                                    "Level": lvl,
                                    "Reward Type": "Card",
                                    "Reward": reward_str,
                                    "Achievement Name (may not match mission)": ach_name
                                })
                            
                            # Item rewards inside achievements
                            for item in reward_node.findall('item'):
                                i_id = item.get('id') or item.text
                                amt = item.get('amount')
                                i_name = item_map.get(i_id, f"Unknown Item ({i_id})")
                                reward_str = f"{amt}x {i_name}" if amt else i_name
                                result_data.append({
                                    "Mission ID": int(m_id) if m_id.isdigit() else m_id,
                                    "Mission Name": m_info["name"],
                                    "Energy": m_info["energy"],
                                    "Row Type": "Achievement Reward",
                                    "Level": lvl,
                                    "Reward Type": "Item",
                                    "Reward": reward_str,
                                    "Achievement Name (may not match mission)": ach_name
                                })
                                
                            # Gold rewards inside achievements (with active global multiplier applied)
                            gold = reward_node.find('gold')
                            if gold is not None and gold.text:
                                base_gold = int(gold.text) if gold.text.isdigit() else 0
                                multiplied_gold = base_gold * GOLD_MULTIPLIER
                                result_data.append({
                                    "Mission ID": int(m_id) if m_id.isdigit() else m_id,
                                    "Mission Name": m_info["name"],
                                    "Energy": m_info["energy"],
                                    "Row Type": "Achievement Reward",
                                    "Level": lvl,
                                    "Reward Type": "Gold",
                                    "Reward": f"{multiplied_gold} Gold",
                                    "Achievement Name (may not match mission)": ach_name
                                })
        except Exception as e:
            print(f"Error parsing achievements.xml: {e}")

    # 5. Sort dataset by Mission ID and Level for a homogeneous presentation
    result_data.sort(key=lambda x: (int(x["Mission ID"]) if str(x["Mission ID"]).isdigit() else 99999, x["Level"]))

    # HTML template containing the user interface framework
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tyrant Unleashed - Missions & Rewards Catalogue</title>
    <style>
        :root {
            --bg-color: #1a1c23;
            --card-bg: #242834;
            --accent-color: #ff9f43;
            --text-color: #e2e8f0;
            --text-muted: #94a3b8;
            --border-color: #3b4256;
            --table-hover: #2d3242;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 20px;
        }

        h1 {
            color: var(--accent-color);
            margin-bottom: 10px;
            font-size: 2.5rem;
        }

        .controls {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            background-color: var(--card-bg);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .controls input, .controls select {
            background-color: var(--bg-color);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            padding: 10px;
            border-radius: 4px;
            font-size: 1rem;
            flex: 1;
        }

        .controls select {
            flex: 0 0 200px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background-color: var(--card-bg);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }

        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        th {
            background-color: #2d3242;
            color: var(--accent-color);
            cursor: pointer;
            user-select: none;
        }

        th:hover {
            background-color: var(--border-color);
        }

        tr:hover {
            background-color: var(--table-hover);
        }

        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: bold;
        }

        .badge-mission { background-color: #2ecc71; color: #fff; }
        .badge-achievement { background-color: #9b59b6; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Tyrant Unleashed</h1>
            <p style="color: var(--text-muted);">Missions & Rewards Catalogue</p>
        </header>

        <div class="controls">
            <input type="text" id="searchInput" placeholder="Search for missions, rewards, etc...">
            <select id="typeFilter">
                <option value="">All Types</option>
                <option value="Mission Reward">Mission Reward</option>
                <option value="Achievement Reward">Achievement Reward</option>
            </select>
        </div>

        <table>
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Mission ID</th>
                    <th onclick="sortTable(1)">Mission Name</th>
                    <th onclick="sortTable(2)">Energy</th>
                    <th onclick="sortTable(3)">Row Type</th>
                    <th onclick="sortTable(4)">Level</th>
                    <th onclick="sortTable(5)">Reward Type</th>
                    <th onclick="sortTable(6)">Reward</th>
                    <th onclick="sortTable(7)">Achievement Name (may not match mission)</th>
                </tr>
            </thead>
            <tbody id="tableBody">
                </tbody>
        </table>
    </div>

    <script>
        // Injection point for processed data
        const data = __DATA_PLACEHOLDER__;

        const tableBody = document.getElementById('tableBody');
        const searchInput = document.getElementById('searchInput');
        const typeFilter = document.getElementById('typeFilter');

        let currentSortCol = -1;
        let sortAsc = true;

        function renderTable(renderData) {
            tableBody.innerHTML = '';
            renderData.forEach(row => {
                const tr = document.createElement('tr');
                const badgeClass = row['Row Type'] === 'Mission Reward' ? 'badge-mission' : 'badge-achievement';
                
                tr.innerHTML = `
                    <td>${row['Mission ID']}</td>
                    <td>${row['Mission Name']}</td>
                    <td>${row['Energy']}</td>
                    <td><span class="badge ${badgeClass}">${row['Row Type']}</span></td>
                    <td>${row['Level']}</td>
                    <td>${row['Reward Type']}</td>
                    <td>${row['Reward']}</td>
                    <td>${row['Achievement Name (may not match mission)'] || '-'}</td>
                `;
                tableBody.appendChild(tr);
            });
        }

        function filterData() {
            const searchTerm = searchInput.value.toLowerCase();
            const selectedType = typeFilter.value;

            const filtered = data.filter(row => {
                const matchesSearch = 
                    String(row['Mission ID']).toLowerCase().includes(searchTerm) ||
                    String(row['Mission Name']).toLowerCase().includes(searchTerm) ||
                    String(row['Reward']).toLowerCase().includes(searchTerm) ||
                    String(row['Reward Type']).toLowerCase().includes(searchTerm) ||
                    String(row['Achievement Name (may not match mission)']).toLowerCase().includes(searchTerm);
                
                const matchesType = !selectedType || row['Row Type'] === selectedType;
                
                return matchesSearch && matchesType;
            });

            renderTable(filtered);
        }

        function sortTable(colIndex) {
            if (currentSortCol === colIndex) {
                sortAsc = !sortAsc;
            } else {
                currentSortCol = colIndex;
                sortAsc = true;
            }

            const keys = [
                'Mission ID', 
                'Mission Name', 
                'Energy', 
                'Row Type', 
                'Level', 
                'Reward Type', 
                'Reward', 
                'Achievement Name (may not match mission)'
            ];
            const key = keys[colIndex];

            data.sort((a, b) => {
                let valA = a[key];
                let valB = b[key];

                if (typeof valA === 'number' && typeof valB === 'number') {
                    return sortAsc ? valA - valB : valB - valA;
                }
                
                valA = String(valA).toLowerCase();
                valB = String(valB).toLowerCase();
                
                if (valA < valB) return sortAsc ? -1 : 1;
                if (valA > valB) return sortAsc ? 1 : -1;
                return 0;
            });

            filterData();
        }

        searchInput.addEventListener('input', filterData);
        typeFilter.addEventListener('change', filterData);

        // Initial setup execution
        renderTable(data);
    </script>
</body>
</html>"""

    # Replace placeholder string with freshly compiled analytical data
    final_html = html_template.replace("__DATA_PLACEHOLDER__", json.dumps(result_data, indent=4, ensure_ascii=False))

    # Save output precisely into index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"Extraction successful. {len(result_data)} entries compiled and embedded directly into 'index.html'.")

if __name__ == "__main__":
    extract_game_data()