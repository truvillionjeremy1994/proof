import os
import numpy as np
import cv2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split

# ---- Load Images ----
def load_images_from_folder(folder, label):
    images = []
    labels = []
    for filename in os.listdir(folder):
        img = cv2.imread(os.path.join(folder, filename))
        if img is not None:
            img = cv2.resize(img, (128, 128))
            images.append(img)
            labels.append(label)
    return images, labels

real_images, real_labels = load_images_from_folder('images/real_augmented', 1)
spoof_images, spoof_labels = load_images_from_folder('images/spoof_augmented', 0)

X = np.array(real_images + spoof_images)
y = np.array(real_labels + spoof_labels)

X = X / 255.0
y = to_categorical(y)

# ---- Split Data ----
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# ---- Build CNN ----
model = Sequential([
    Conv2D(32, (3,3), activation='relu', input_shape=(128, 128, 3)),
    MaxPooling2D(2, 2),
    Conv2D(64, (3,3), activation='relu'),
    MaxPooling2D(2, 2),
    Flatten(),
    Dense(64, activation='relu'),
    Dense(2, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test))

# ---- Save Model ----
model.save("smartid_model.h5")
print("✅ Model saved as smartid_model.h5")