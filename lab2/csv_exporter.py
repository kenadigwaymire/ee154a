import csv


headers = [
    ['ABS TIME', 
     'T1', 'T2', 'T3', 'T4', 'T5', 
     'X ACC', 'Y ACC', 'Z ACC', 
     'X GYRO', 'Y GYRO', 'Z GYRO', 
     'X MAG', 'Y MAG', 'Z MAG',]]

with open('lab2.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter='|')
    writer.writerows(headers)

    count = 0
    while count < 100:
        # Read data from sensors
        ABS_TIME = count
        T1 = 0
        T2 = 0
        T3 = 0
        T4 = 0
        T5 = 0
        X_ACC = 0
        Y_ACC = 0
        Z_ACC = 0
        X_GYRO = 0
        Y_GYRO = 0
        Z_GYRO = 0
        X_MAG = 0
        Y_MAG = 0
        Z_MAG = 0

        # Save data to CSV
        data = [[ABS_TIME, 
                T1, T2, T3, T4, T5, 
                X_ACC, Y_ACC, Z_ACC, 
                X_GYRO, Y_GYRO, Z_GYRO, 
                X_MAG, Y_MAG, Z_MAG]]
        
        writer.writerows(data)

        count += 1
        if count >= 100:
            break