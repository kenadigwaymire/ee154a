import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

try:
    df = pd.read_csv('lab2.csv')
except FileNotFoundError:
    print(f'File not found')
    exit()

df.replace(0, np.nan, inplace=True)

df['ABS TIME'] = pd.to_datetime(df['ABS TIME'])

plt.figure(figsize=(10, 6))
plt.plot(df['ABS TIME'], df['T-CPU'], label = 'T-CPU')
plt.plot(df['ABS TIME'], df['T-PCB-TOP'], label = 'T-PCB-TOP')
plt.plot(df['ABS TIME'], df['T-PCB-BOTTOM'], label = 'T-PCB-BOTTOM')
plt.plot(df['ABS TIME'], df['T-WIRELESS-MODEM'], label = 'T-WIRELESS-MODEM')
plt.plot(df['ABS TIME'], df['T-POWER-MANAGER'], label = 'T-POWER-MANAGER')
plt.title('Temperature Plot')
plt.xlabel('Time [s]')
plt.ylabel('Temperature [C]')
plt.legend()
plt.savefig('temp_plot.png')

plt.figure(figsize=(10, 6))
plt.plot(df['ABS TIME'], df['X ACC'], label = 'X Acc')
plt.plot(df['ABS TIME'], df['Y ACC'], label = 'Y Acc')
plt.plot(df['ABS TIME'], df['Z ACC'], label = 'Z Acc')
plt.title('Acceleration Plot')
plt.xlabel('Time [s]')
plt.ylabel('Acceleration [m/s^2]')
plt.legend()
plt.savefig('acc_plot.png')

plt.figure(figsize=(10, 6))
plt.plot(df['ABS TIME'], df['X GYRO'], label = 'X Gyro')
plt.plot(df['ABS TIME'], df['Y GYRO'], label = 'Y Gyro')
plt.plot(df['ABS TIME'], df['Z GYRO'], label = 'Z Gyro')
plt.title('Gyroscope Plot')
plt.xlabel('Time [s]')
plt.ylabel('Angle [rad]')
plt.legend()
plt.savefig('gyro_plot.png')

plt.figure(figsize=(10, 6))
plt.plot(df['ABS TIME'], df['X MAG'], label = 'X Mag')
plt.plot(df['ABS TIME'], df['Y MAG'], label = 'Y Mag')
plt.plot(df['ABS TIME'], df['Z MAG'], label = 'Z Mag')
plt.title('Magnetometer Plot')
plt.xlabel('Time [s]')
plt.ylabel('Magnetic Field Intensity [T]')
plt.legend()
plt.savefig('gyro_plot.png')