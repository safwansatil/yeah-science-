# SECTION 05: Know What the Score Means

## 1. Machine Learning Fundamentals for Embedded Devices (TinyML)
* **What TinyML is about**: Standard deep learning models require heavy GPUs, but microcontrollers (like ESP32/STM32) have very limited RAM (KBs to MBs) and compute power. TinyML focuses on taking trained neural networks, shrinking them down (via quantization and pruning), and running inference locally on microcontrollers without needing cloud connectivity.
* **Model Training vs. Inference**: Training happens on powerful computers using datasets and backpropagation to learn weights. Inference is simply using those pre-calculated weights on new data to make predictions—which is what runs directly on the rover's embedded board.

---

## 2. Decision Thresholds & Confusion Matrix
* **Confusion Matrix**: A simple 2x2 grid that compares real ground truth against model predictions:
  * **True Positive (TP)**: Model predicted a target flag, and it WAS a target flag.
  * **True Negative (TN)**: Model predicted empty terrain, and it WAS empty terrain.
  * **False Positive (FP)**: Model predicted a target flag, but it was just a rock (False Alarm).
  * **False Negative (FN)**: Model missed a real target flag (Missed Detection).
* **Thresholding**: Models output a probability score between `0.0` and `1.0`. Setting the threshold high (e.g., `0.85`) means the model only flags items it is super confident about (reduces false alarms, but misses some targets). Setting it low (e.g., `0.30`) catches every target but increases false alarms.

---

## 3. Precision, Recall, and Accuracy Trade-offs
* **Accuracy**: $\frac{TP + TN}{\text{Total Predictions}}$. Can be misleading if $99\%$ of the camera frame is empty ground (class imbalance).
* **Precision**: $\frac{TP}{TP + FP}$. "When the model claims it saw a target flag, how often is it actually right?"
* **Recall**: $\frac{TP}{TP + FN}$. "Out of all actual target flags in front of the rover, how many did the model catch?"
* **The Trade-off**: Increasing precision usually drops recall, and vice-versa. For a rover, high recall is critical when detecting severe terrain drops (must catch every cliff!), while high precision is preferred when logging science targets so the arm doesn't attempt to scoop random rocks.

---

## 4. YOLO Object Detection Metrics
* **IoU (Intersection over Union)**: Measures how accurately the predicted bounding box matches the ground truth box:
  $$\text{IoU} = \frac{\text{Area of Overlap}}{\text{Area of Union}}$$
* **mAP50 (Mean Average Precision at IoU threshold 0.50)**: Evaluates overall detection accuracy across classes when a bounding box overlap of $\ge 50\%$ is considered a success.
* **mAP50-95**: Average performance across multiple strictness levels (IoU thresholds from $0.50$ to $0.95$ in $0.05$ steps), showing how tightly and reliably the bounding boxes fit the real objects.

---

## 5. What Was Confusing & What I Want to Learn More
* **Unclear / Confusing Topic**: Understanding how quantizing floating-point weights down to 8-bit integers (`int8`) impacts model precision without breaking feature representation.
* **To Explore Further**: Learning how ROS2 nodes interface directly with TensorRT/NPU hardware accelerators on the Jetson Orin Nano for real-time video stream detection.