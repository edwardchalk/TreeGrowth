import math
import datetime
import matplotlib.pyplot as plt
from typing import Dict, Any

# The base class for the triadic design philosophy
class DynamicAspect:
    pass

# The EnergyAspect deals with the energy requirements and production of the tree, primarily through photosynthesis.
class EnergyAspect(DynamicAspect):
    def __init__(self, input: Dict[str, Any], state: Dict[str, Any], output: Dict[str, Any], latitude: float, initial_nutrients: float = 100.0):
        super().__init__()
        self.input = input
        self.state = state
        self.output = output
        self.latitude = latitude
        # Leaves play a crucial role in photosynthesis, this variable indicates if the tree has leaves or not.
        self.has_leaves = True
        self.state["stored_nutrients"] = initial_nutrients
        self.state["tree_size"] = 1.0  # "1" represents the initial size of the tree.

    # Photosynthesis is a key energy-generating mechanism for trees. It uses sunlight to convert CO2 and water into sugars.
    def photosynthesis(self, day_of_year, temperature, humidity, CO2_concentration, a=1):
        if not self.has_leaves:
            return 0
        
        # Optimum conditions for photosynthesis are considered to be 25°C for temperature and 50% for humidity. 
        # The further away from these values, the lower the photosynthesis efficiency.
        temperature_factor = max(0, 1 - abs(25 - temperature) * 0.05)
        humidity_factor = max(0, 1 - abs(50 - humidity) * 0.01)
        
        # CO2 is vital for photosynthesis. As the CO2 concentration increases from the "normal" atmospheric level (400 parts per million),
        # photosynthesis rate can increase since plants have more CO2 to work with.
        CO2_factor = CO2_concentration / 400
        
        # Calculate the day length based on latitude and time of year.
        # This is important because photosynthesis can only occur during daylight hours.
        latitude_rad = math.radians(self.latitude)
        seasonal_factor = math.cos(2 * math.pi * day_of_year / 365.25)
        D = 12 * (1 + math.cos(latitude_rad * seasonal_factor))

        # Declination and solar intensity factors ensure the angle and intensity of sunlight are accounted for.
        declination = 23.44 * math.sin(2 * math.pi * (day_of_year + 10) / 365.25)
        declination_rad = math.radians(declination)
        I = math.cos(latitude_rad - declination_rad)

        # Trees with larger canopies capture more sunlight, hence the photosynthesis multiplication factor.
        leaf_area_multiplier = 1 + 0.1 * self.state["tree_size"]
        
        # The resulting value is a composite of all these factors.
        return a * D * I * temperature_factor * humidity_factor * CO2_factor * leaf_area_multiplier

    # Water requirement varies with temperature.
    def water_requirement(self, temperature):
        base_requirement = 40 / 7
        if temperature > 30:
            return base_requirement * 1.5
        elif temperature < 15:
            return base_requirement * 0.75
        return base_requirement

    # Captures energy consumption for respiration and growth of the tree.
    def respiration_and_growth(self):
        # Respiration rate is proportional to tree size.
        respiration_rate = 0.05 * self.state["tree_size"]
        
        # Bud/root growth depends on nutrient availability.
        bud_root_growth_rate = 0.02 * self.state["stored_nutrients"] if self.state["stored_nutrients"] > 20 else 0

        # Total consumption is the sum of respiration and growth.
        total_consumption = respiration_rate + bud_root_growth_rate
        self.state["stored_nutrients"] -= total_consumption

        # Increase tree size only if there are sufficient nutrients for growth
        if self.state["stored_nutrients"] > 20:
            self.state["tree_size"] += 0.01

        return total_consumption      

    # Integrates the photosynthesis and respiration processes.
    def generate_energy(self, sunlight, water, day_of_year, temperature, humidity, CO2_concentration):
        # Initial assumption is that energy generation is 0.
        if self.has_leaves:
            # Only if the tree has leaves, will it perform photosynthesis.
            photosynthesis_efficiency = self.photosynthesis(day_of_year, temperature, humidity, CO2_concentration)
            energy_generated = sunlight * water * 0.1 * photosynthesis_efficiency
            self.state["stored_nutrients"] += energy_generated
        
        total_consumption = self.respiration_and_growth()
        net_energy = 0 if not self.has_leaves else (energy_generated - total_consumption)
        
        return net_energy

# Logic aspect deals with the tree's internal logic that decides growth and fruit production.
class LogicAspect(DynamicAspect):
    def __init__(self, input: Dict[str, Any], state: Dict[str, Any], output: Dict[str, Any]):
        super().__init__()
        self.input = input
        self.state = state
        self.output = output
    
    def seasonal_multiplier(self, day_of_year):
        return 1 - 0.8 * (math.cos(math.pi * day_of_year / 182.5))
 

    # Determines how the tree will grow and if it will produce fruit based on the current conditions, tree age, and health.
    def decide_growth_and_fruit_production(self, stored_nutrients, day_of_year, tree_age, tree_size, health):  
        # The growth rate is influenced by the tree's current size and the amount of stored nutrients.
        growth_multiplier = 1 + 0.05 * tree_size
        growth_multiplier *= health  # Modifying the growth multiplier based on the tree's health

        # The seasonal multiplier uses the time of year to represent the fact that growth may be better during certain seasons.
        growth_rate = stored_nutrients * 0.1 * self.seasonal_multiplier(day_of_year) * growth_multiplier
        fruit_count = 0

        # Modelling a tree that starts producing fruit after 3 years and continues until 5 years.
        # The fruit production is also influenced by the stored nutrients and the time of year.
        if 150 <= day_of_year <= 250 and stored_nutrients > 10 and 3 <= tree_age <= 5:
            fruit_production_multiplier = max(0.5, health)  # Trees in better health produce more fruits
            fruit_count = int(stored_nutrients // 10 * fruit_production_multiplier)  # Using int() to ensure whole fruits
            # Producing fruits consumes stored nutrients.
            stored_nutrients -= fruit_count * 0.5

        return growth_rate, stored_nutrients, fruit_count

# Control aspect assesses the overall health of the tree.
class ControlAspect(DynamicAspect):
    def __init__(self, input: Dict[str, Any], state: Dict[str, Any], output: Dict[str, Any]):
        super().__init__()
        self.input = input
        self.state = state
        self.output = output
    
    def assess_health(self, stored_nutrients, disease_factor):
        health = 1.0  # Assuming full health initially
        health -= disease_factor  # Reduce health by disease factor
        if stored_nutrients < 10:  # If nutrients are too low, health decreases
            health -= 0.1
        return health

# The Tree class integrates all the aspects and represents a holistic model of a tree.
class Tree:
    def __init__(self, latitude, initial_nutrients: float = 800.0):
        self.age = 0
        self.triadic_aspect = {
            "energy": EnergyAspect({}, {"stored_nutrients": 0, "tree_size": 1.0}, {}, latitude, initial_nutrients),
            "logic": LogicAspect({}, {}, {}),
            "control": ControlAspect({}, {"health": 1.0}, {})
        }
    
    def daily_update(self, sunlight, water, day_of_year, temperature, humidity, CO2_concentration, disease_factor):
        self.age += 1/365  # Age the tree by one day
        self.triadic_aspect["energy"].has_leaves = not (330 <= day_of_year <= 365 or 1 <= day_of_year <= 60)
        self.triadic_aspect["energy"].generate_energy(sunlight, water, day_of_year, temperature, humidity, CO2_concentration)
        stored_nutrients = self.triadic_aspect["energy"].state["stored_nutrients"]
        health = self.triadic_aspect["control"].assess_health(stored_nutrients, disease_factor)
        
        tree_size = self.triadic_aspect["energy"].state["tree_size"]
        growth_rate, updated_nutrients, fruit_count = self.triadic_aspect["logic"].decide_growth_and_fruit_production(stored_nutrients, day_of_year, self.age, tree_size, health)  # Passing health as an argument
        
        self.triadic_aspect["energy"].state["stored_nutrients"] = updated_nutrients
        self.triadic_aspect["energy"].output["growth_rate"] = growth_rate
        self.triadic_aspect["logic"].output["fruit_count"] = fruit_count
        self.triadic_aspect["control"].state["health"] = health
        self.triadic_aspect["control"].output["health_status"] = "Healthy" if health >= 0.9 else ("Unhealthy" if health <= 0.6 else "Average")

    def get_data(self):
        energy_data = {
            "stored_nutrients": self.triadic_aspect["energy"].state["stored_nutrients"],
            "growth_rate": self.triadic_aspect["energy"].output["growth_rate"],
            "tree_size": self.triadic_aspect["energy"].state["tree_size"]
        }

        logic_data = {
            "fruit_count": self.triadic_aspect["logic"].output["fruit_count"]
        }

        control_data = {
            "health": self.triadic_aspect["control"].state["health"],
            "health_status": self.triadic_aspect["control"].output["health_status"]
        }

        return {
            "age": self.age,
            "energy": energy_data,
            "logic": logic_data,
            "control": control_data
        }

# The simulation function simulates the growth of a tree over a set number of years.
def simulate_growth(years=5):
    # Latitude is set to represent London, UK. Latitude can influence sunlight duration and intensity.
    latitude = 51.509865
    tree = Tree(latitude,50)

    # The simulation runs for a set number of days, assuming no leap years.
    total_days = years * 365
    
    days = range(1, total_days + 1)
    stored_nutrients_list, growth_rate_list, fruit_count_list, health_list = [], [], [], []

    for day in days:
        # For simplicity, the following parameters are kept constant for each day in the simulation.
        # Real-world applications would involve more variability and be sourced from weather data sets.
        sunlight = 1.0  # assuming full sunlight
        water = 1.0  # assuming enough water
        temperature = 20  # in Celsius
        humidity = 50  # in percentage
        CO2_concentration = 400  # in ppm
        disease_factor = 0.0  # 0 for no disease, 1 for highest disease factor
        
        day_of_year = (day - 1) % 365 + 1  # Convert the day of the total simulation to the day of the current year
        tree.daily_update(sunlight, water, day_of_year, temperature, humidity, CO2_concentration, disease_factor)

        data = tree.get_data()
        stored_nutrients_list.append(data["energy"]["stored_nutrients"])
        growth_rate_list.append(data["energy"]["growth_rate"])
        fruit_count_list.append(data["logic"]["fruit_count"])
        health_list.append(data["control"]["health"])

    # This section generates a visual representation of the tree's growth over the given number of years.
    fig, ax1 = plt.subplots(figsize=(12, 8))

    # Plotting stored nutrients and growth rate on the primary y-axis
    ax1.plot(days, stored_nutrients_list, label="Stored Nutrients", color='g')
    ax1.plot(days, growth_rate_list, label="Growth Rate", color='b')
    ax1.set_ylabel('Value')
    ax1.set_xlabel('Days (Over {} Years)'.format(years))
    ax1.legend(loc='upper left')

    # Create a second y-axis and plot fruit count and health on it
    ax2 = ax1.twinx()
    ax2.plot(days, fruit_count_list, label="Fruit Count", color='c', linestyle='dashed')
    ax2.plot(days, health_list, label="Health", color='m', linestyle='dotted')
    ax2.set_ylabel('Value')
    ax2.legend(loc='upper right')

    plt.title("Tree Growth Simulation over {} Years".format(years))
    plt.grid(True)
    plt.show()

#Run the simulation over the course of 5 years
simulate_growth(5)
