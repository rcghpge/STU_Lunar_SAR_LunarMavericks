import json
import os

def modify_json(file_path, location_number):
  """
  Modifies the JSON file to set the "CrashedLunarLander" location.

  Args:
    file_path: Path to the JSON file.
    location_number: Integer (1-6) representing the location option.
  """
  try:
    with open(file_path, 'r') as f:
      data = json.load(f)

    location_keys = {
        1: "PossibleLocation_CraterRim",
        2: "PossibleLocation1",
        3: "PossibleLocation2",
        4: "PossibleLocation3",
        5: "PossibleLocation4",
        6: "PossibleLocation5"
    }

    seed_start_idx = {
      1: 0,
      2: 0,
      3: 2592,
      4: 2751,
      5: 3056,
      6: 931
    }

    if location_number in location_keys:
      new_location = location_keys[location_number]

      new_seed_start = seed_start_idx[location_number]

      try:
        new_coords = data["DataManager"]["SimEntity"]["CrashedLanderLocationOptions"][new_location]
        print("New coordinates:", new_coords)

        # Apply different obstacle spawning seeds
        systems = data["SystemManager"].get("Systems", [])
        for i, system in enumerate(systems):
          if system.get("Nametag") == "ProceduralRocks11":
            system["Inst_Parameters"]["Seed_lat"] = ["int32", new_seed_start + 0]
            system["Inst_Parameters"]["Seed_lon"] = ["int32", new_seed_start + 1]
            system["Inst_Parameters"]["Seed_azimuth"] = ["int32", new_seed_start + 2]
            system["Inst_Parameters"]["Seed_scale"] = ["int32", new_seed_start + 3]
            print("SeedStart updated successfully!")
          if system.get("Nametag") == "ProceduralRocks10":
            system["Inst_Parameters"]["Seed_lat"] = ["int32", new_seed_start + 4]
            system["Inst_Parameters"]["Seed_lon"] = ["int32", new_seed_start + 5]
            system["Inst_Parameters"]["Seed_azimuth"] = ["int32", new_seed_start + 6]
            system["Inst_Parameters"]["Seed_scale"] = ["int32", new_seed_start + 7]
            print("SeedStart updated successfully!")

        # Search for the "CrashedLunarLander" entity
        entities = data.get("DataManager", {}).get("entities", [])
        crashed_lander_found = False
        for i, entity in enumerate(entities):
          if entity.get("#Required", {}).get("Name") == "CrashedLunarLander":
            print("Found CrashedLunarLander at index:", i)
            crashed_lander_found = True

            from_template = entity.get("#FromTemplate", {})
            if from_template:
              param_overrides = from_template.get("ParamOverrides", {})
              if param_overrides:
                param_overrides["Location"] = new_coords
                print(f"JSON file updated successfully! New location: {new_location}")
              else:
                print("Error: 'ParamOverrides' not found in '#FromTemplate'")
            else:
              print("Error: '#FromTemplate' not found in CrashedLunarLander entity")
            break  # Exit the loop once found

        if not crashed_lander_found:
          print("Error: 'CrashedLunarLander' entity not found.")

      except KeyError as e:
        print(f"KeyError: {e}")

    else:
      print("Invalid location number. Please enter a number between 1 and 6.")
      return

    with open(file_path, 'w') as f:
      json.dump(data, f, indent=4)

  except FileNotFoundError:
    print("File not found: " + file_path)
  except json.JSONDecodeError:
    print("Invalid JSON format in " + file_path)
  except Exception as e:
    print("An error occurred: " + str(e))

if __name__ == "__main__":
  file_path = "sims\STU_BaseSimFinal.json"
  print("Available locations:")

  # location_keys is defined here, so it's accessible in this block
  location_keys = {  
      1: "PossibleLocation_CraterRim",
      2: "PossibleLocation1",
      3: "PossibleLocation2",
      4: "PossibleLocation3",
      5: "PossibleLocation4",
      6: "PossibleLocation5"
  }

  for i in range(1, 7):
    print(f"{i}: {list(location_keys.values())[i-1]}")

  while True:
    try:
      location_number = int(input("Enter the desired location number (1-6): "))
      break
    except ValueError:
      print("Invalid input. Please enter a number.")

  modify_json(file_path, location_number)
  # input("Press Enter to exit...") #not necessary when ran from .bat