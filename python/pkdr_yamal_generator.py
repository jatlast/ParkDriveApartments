def generate_ha_sql_yaml():
    buildings = [41, 42, 43, 44]
    apartments = list(range(1, 17))  # Keep SQL apartment numbers unpadded
    db_url = "!secret pkdr_sql_db_url"
    
    yaml_output = "sql:\n"
    
    for b in buildings:
        yaml_output += f"  # Building {b - 40}\n"
        yaml_output += f"  - name: B{b - 40} Temperature\n"
        yaml_output += f"    query: >\n"
        yaml_output += f"      SELECT ROUND((temperature * 9/5) + 32, 2) AS temperature\n"
        yaml_output += f"      FROM PkDr.Thermostats\n"
        yaml_output += f"      WHERE apt = {b}\n"
        yaml_output += f"        AND temperature BETWEEN 50 AND 122\n"
        yaml_output += f"        AND taken >= NOW() - INTERVAL 30 MINUTE\n"
        yaml_output += f"      ORDER BY taken DESC\n"
        yaml_output += f"      LIMIT 1;\n"
        yaml_output += f"    column: temperature\n"
        yaml_output += f"    unit_of_measurement: '°F'\n"
        yaml_output += f"    db_url: {db_url}\n\n"
        yaml_output += f"  - name: B{b - 40} Humidity\n"
        yaml_output += f"    query: >\n"
        yaml_output += f"      SELECT ROUND(humidity, 1) AS humidity\n"
        yaml_output += f"      FROM PkDr.Thermostats\n"
        yaml_output += f"      WHERE apt = {b}\n"
        yaml_output += f"      ORDER BY taken DESC\n"
        yaml_output += f"      LIMIT 1;\n"
        yaml_output += f"    column: humidity\n"
        yaml_output += f"    unit_of_measurement: '%'\n"
        yaml_output += f"    db_url: {db_url}\n\n"
        for apt in apartments[(b - 41) * 4:(b - 40) * 4]:  # Select the correct set of 4 apartments per building
            apt_padded = f"{apt:02d}"  # Pad only for YAML names
            yaml_output += f"  - name: Apt{apt_padded} Temperature\n"
            yaml_output += f"    query: >\n"
            yaml_output += f"      SELECT ROUND((temperature * 9/5) + 32, 2) AS temperature\n"
            yaml_output += f"      FROM PkDr.Thermostats\n"
            yaml_output += f"      WHERE apt = {apt}\n"
            yaml_output += f"        AND temperature BETWEEN 50 AND 122\n"
            yaml_output += f"        AND taken >= NOW() - INTERVAL 30 MINUTE\n"
            yaml_output += f"      ORDER BY taken DESC\n"
            yaml_output += f"      LIMIT 1;\n"
            yaml_output += f"    column: temperature\n"
            yaml_output += f"    unit_of_measurement: '°F'\n"
            yaml_output += f"    db_url: {db_url}\n\n"
            yaml_output += f"  - name: Apt{apt_padded} Humidity\n"
            yaml_output += f"    query: >\n"
            yaml_output += f"      SELECT ROUND(humidity, 1) AS humidity\n"
            yaml_output += f"      FROM PkDr.Thermostats\n"
            yaml_output += f"      WHERE apt = {apt}\n"
            yaml_output += f"      ORDER BY taken DESC\n"
            yaml_output += f"      LIMIT 1;\n"
            yaml_output += f"    column: humidity\n"
            yaml_output += f"    unit_of_measurement: '%'\n"
            yaml_output += f"    db_url: {db_url}\n\n"
    
    return yaml_output

# Generate YAML configuration
yaml_config = generate_ha_sql_yaml()
print(yaml_config)
