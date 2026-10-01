# SECTION 04: Ranging Beyond the Wall

## 1. From Dispatch to Arrival

### Control Signal Flow (Dispatch)
1. **Operator Input**: The operator presses a key (e.g., `W` for forward) or moves a joystick on the Ground Station UI (PySide6 / QML app)[cite: 10].
2. **Packet Transmission**: The UI packages the velocity request into a telemetry packet and transmits it over the HM30 Digital HD Radio Link[cite: 10].
3. **Primary Compute Ingestion**: The onboard Nvidia Jetson Orin Nano receives the radio packet and ROS2 passes the command layer to the drive controller[cite: 10].
4. **Drive MCU Generation**: The Jetson sends direction and speed instructions over UART/CAN to the Drive MCU (ESP32/STM32)[cite: 10].
5. **Motor Execution**: The Drive MCU generates PWM speed signals and Digital Direction signals sent to the Dual H-Bridge Motor Drivers, which deliver power to the 24V DC planetary gearbox motors, turning the wheels[cite: 10].

### Feedback Verification (Arrival)
The operator knows the rover actually moved through two feedback loops:
* **Closed-Loop Telemetry**: High-frequency wheel quadrature encoders (~1000 PPR) and the 9-DOF IMU transmit pulse ticks and acceleration data back to the Drive MCU/Jetson[cite: 10, 11]. The telemetry data travels back through the radio link to update wheel odometry indicators on the Ground UI[cite: 10, 11].
* **Visual Confirmation**: The onboard forward USB HD camera streams live 1080p@30 FPS video back to the Ground Station UI screen, giving the operator real-time visual confirmation of ground movement[cite: 10, 11].

---

## 2. The Sensor Court

* **Sensor Selected**: Wheel Encoders (Quadrature Encoders, ~1000 PPR)[cite: 11]
* **What it tells the rover**: Provides precise short-term wheel rotation distance and speed measurements for relative odometry calculations[cite: 11].
* **How it gets confused on rough terrain**: Wheel encoders measure wheel rotation, NOT ground displacement[cite: 11]. When driving on loose sand or gravel, wheel slippage occurs—the wheels spin rapidly without moving the chassis forward at the expected speed[cite: 10, 11]. This causes the rover's computer to calculate false odometry, falsely assuming it has traveled much farther than it actually has[cite: 11].

---

## 3. Chain of Command

* **Who wins?**: Manual operator control (Teleop) MUST always win over autonomous navigation[cite: 11].
* **Why?**: Safety and human override take absolute priority over algorithmic execution to prevent crashes, equipment damage, or hazardous operations[cite: 11].
* **Simple, Safe Handling Strategy**:
  1. **Command Preemption Intercept**: Implement a priority multiplexer/topic mux in ROS2 where manual joystick or WASD inputs instantly override autonomous motor command streams[cite: 10, 11].
  2. **Automatic State Switch**: Entering manual control instantly cancels active autonomous goal states and drops autonomy mode back to `STANDBY`.
  3. **No Silent Resumes**: Once manual override is triggered, autonomy cannot resume automatically; the operator must explicitly re-engage autonomous execution[cite: 11].

---

## 4. The Frostfangs Gravel Case

* **Explanation of Disagreement**: The 8-meter drift calculated by the computer is caused by wheel encoder slippage on the loose gravel[cite: 11]. The wheels spun on the gravel, making the wheel odometry engine compute an erroneous positional offset, whereas the camera feed represents reality[cite: 10, 11].
* **What to check before deciding what to do next**:
  1. **Visual Alignment vs. Map Checks**: Verify the camera target detection overlay against the RTK GPS receiver global positioning data[cite: 10, 11].
  2. **IMU Heading & Acceleration**: Inspect 9-DOF IMU data to verify whether actual lateral acceleration or heading deviation matches the reported 8-meter drift[cite: 11].
  3. **Odometry Reset**: Clear/reset the local encoder odometry frame to align with the camera/GPS reference frame[cite: 11].
  4. **Manual Intervention**: Switch to manual teleop mode if the gravel slope poses an immediate rollover risk[cite: 10, 11].