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
plt.plot(df['ABS TIME'], df['T1'], label = 'T1')
plt.plot(df['ABS TIME'], df['T2'], label = 'T2')
plt.plot(df['ABS TIME'], df['T3'], label = 'T3')
plt.plot(df['ABS TIME'], df['T4'], label = 'T4')
plt.plot(df['ABS TIME'], df['T5'], label = 'T5')
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