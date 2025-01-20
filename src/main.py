import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv("data/Performance.csv")

# Basic stats
print("Summary Statistics:")
print(data.describe())

# Plot FPS over time
plt.plot(data['Time Stamp'], data['FPS'], marker='o', label='FPS')
plt.title('FPS Over Time')
plt.xlabel('Time (seconds)')
plt.ylabel('FPS')
plt.legend()
plt.grid()
plt.show()

