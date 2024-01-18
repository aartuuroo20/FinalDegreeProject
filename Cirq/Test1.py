import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import pandas as pd
import tensorflow_quantum as tfq
import tensorflow as tf
import cirq
import sympy
import random

from DataSet import DataSet
from sklearn.preprocessing import MinMaxScaler

def hinge_accuracy(y_true, y_pred):
    y_true = tf.squeeze(y_true) > 0.0
    y_pred = tf.squeeze(y_pred) > 0.0
    result = tf.cast(y_true == y_pred, tf.float32)

    return tf.reduce_mean(result)


class CircuitLayerBuilder():
    def __init__(self, data_qubits, readout):
        self.data_qubits = data_qubits
        self.readout = readout

    def add_layer(self, circuit, gate, prefix):
        for i, qubit in enumerate(self.data_qubits):
            symbol = sympy.Symbol(prefix + '-' + str(i))
            circuit.append(gate(qubit, self.readout)**symbol)

def create_quantum_model(num_layers=1):
    """Create a QNN model circuit and readout operation to go along with it."""
    data_qubits = cirq.GridQubit.rect(4, 4)  # a 4x4 grid.
    readout = cirq.GridQubit(-1, -1)         # a single qubit at [-1,-1]
    circuit = cirq.Circuit()
    
    builder = CircuitLayerBuilder(
        data_qubits = data_qubits,
        readout=readout)

    for i in range(num_layers):
        builder.add_layer(circuit, cirq.ZZ, "zz1{}".format(i + 1))
        builder.add_layer(circuit, cirq.XX, "xx{}".format(i + 1))

    return circuit, cirq.Z(readout)


########################################################################################################################33


df = pd.read_csv("/home/arturo/Downloads/heart.csv")
print(df.head())

target_column = "output"
numerical_column = df.columns.drop(target_column)
output_rows = df[target_column]
df.drop(target_column,axis=1,inplace=True)

scaler = MinMaxScaler()
scaler.fit(df)
t_df = scaler.transform(df)

X_train, X_test, y_train, y_test = train_test_split(t_df, output_rows, test_size=0.25, random_state=0)

########################################################################################################################33

circuit, readout = create_quantum_model()
print(circuit)
print(readout)

inputs = tf.keras.Input(shape=(), dtype=tf.dtypes.string)

# Convierte los circuitos cuánticos a tensores de tipo string
X_train_strings = tfq.convert_to_tensor([circuit for _ in range(len(X_train))])
X_test_strings = tfq.convert_to_tensor([circuit for _ in range(len(X_test))])

########################################################################################################################33

layer = tfq.layers.PQC(circuit, readout)(inputs)

out = (layer + 1) / 2
model = tf.keras.Model(inputs=inputs, outputs=out)
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.02),
                loss=tf.keras.losses.hinge,
                metrics=[hinge_accuracy])

history = model.fit(
      X_train_strings, y_train,
      batch_size=9,
      epochs=3,
      verbose=1,
      validation_data=(X_test_strings, y_test))


print(model.trainable_weights)

########################################################################################################################33

plt.plot(history.history['loss'], label='Training')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.legend()
plt.title("Training Loss")
plt.xlabel("Epochs")
plt.ylabel("Hinge Loss")
plt.show()

plt.plot(history.history['hinge_accuracy'], label='Training')
plt.plot(history.history['val_hinge_accuracy'], label='Validation Acc')
plt.legend()
plt.title("Training Acc")
plt.xlabel("Epochs")
plt.ylabel("Accuracy")
plt.show()