import numpy as np
from sklearn.model_selection import train_test_split
from keras import *
import tensorflow as tf


def cnn_encoder(num):
    encoder_input = Input(shape=(10, 16), name=f"input_{num}")
    x = layers.Conv1D(filters=16, kernel_size=3, activation='relu')(encoder_input)
    x = layers.Dropout(0.3)(x)
    x = layers.Flatten()(x)
    encoder_output = layers.Reshape((8, 16))(x)
    return Model(encoder_input, encoder_output, name=f"cnn_encoder_{num}")


def lstm_layer():
    lstm_input = Input(shape=(768, 1), name="lstm_input")
    x = layers.LSTM(5, input_shape=(192, 4), return_sequences=False)(lstm_input)
    x = layers.Dropout(0.3)(x)
    lstm_output = layers.Dense(5, activation='softmax')(x)
    return Model(lstm_input, lstm_output, name="lstm_layer")


def categorization(data):
    inputs = Input(shape=(40, 16), name="input")
    y_1 = cnn_encoder(1)(inputs[:, :-30, :])
    y_2 = cnn_encoder(2)(inputs[:, 10:-20, :])
    y_3 = cnn_encoder(3)(inputs[:, 20:-10, :])
    y_4 = cnn_encoder(4)(inputs[:, 30:, :])
    lstm_input = layers.Concatenate(axis=1)([y_1, y_2, y_3, y_4])
    x = layers.LSTM(16, return_sequences=True)(lstm_input)
    x = layers.GlobalAvgPool1D()(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(10)(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(5)(x)
    outputs = layers.Activation('softmax')(x)
    model = Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='adam',
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])
    model.load_weights('../data/category_model/model_weight.h5')
    predit = model.predict(data)
    category_list = []
    for i in predit:
        a = np.array(i)
        category = a.argmax()
        if category == 0:
            category_list.append(0)
        elif category == 1:
            category_list.append(1)
        elif category == 2:
            category_list.append(2)
        elif category == 3:
            category_list.append(3)
        elif category == 4:
            category_list.append(4)
    a = 1
    return category_list


if __name__ == "__main__":
    with tf.device('/cpu:0'):
        data = np.load("../data/data.npy")
        label = np.load("../data/label.npy")
        x_train, x_valid, y_train, y_valid = train_test_split(data, label, test_size=0.2, shuffle=True, stratify=label,
                                                              random_state=77)
        inputs = Input(shape=(40, 16), name="input")
        y_1 = cnn_encoder(1)(inputs[:, :-30, :])
        y_2 = cnn_encoder(2)(inputs[:, 10:-20, :])
        y_3 = cnn_encoder(3)(inputs[:, 20:-10, :])
        y_4 = cnn_encoder(4)(inputs[:, 30:, :])
        lstm_input = layers.Concatenate(axis=1)([y_1, y_2, y_3, y_4])
        x = layers.LSTM(16, return_sequences=True)(lstm_input)
        x = layers.GlobalAvgPool1D()(x)
        x = layers.Dropout(0.2)(x)
        x = layers.Dense(10)(x)
        x = layers.Dropout(0.3)(x)
        x = layers.Dense(5)(x)
        outputs = layers.Activation('softmax')(x)
        model = Model(inputs=inputs, outputs=outputs)
        model.summary()

        model.compile(optimizer='adam',
                      loss='categorical_crossentropy',
                      metrics=['accuracy'])
        early_stopping = callbacks.EarlyStopping(monitor='val_accuracy', min_delta=0.001, baseline=0.95, verbose=1, patience=100)
        history = model.fit(
            x_train, y_train,
            epochs=200,
            validation_data=(x_valid, y_valid),
            shuffle=True,
            callbacks = [early_stopping]
        )

        loss, acc = model.evaluate(x_valid, y_valid)
        print("\nLoss: %f, Acc: %f" % (loss, acc))

        model.save('../data/category_model/save_model.h5')
        model.save_weights('../data/category_model/model_weight.h5')
        import matplotlib.pyplot as plt

        fig, loss_ax = plt.subplots()
        acc_ax = loss_ax.twinx()

        loss_ax.plot(history.history['loss'], 'y', label='train loss')
        loss_ax.plot(history.history['val_loss'], 'r', label='val loss')
        loss_ax.set_xlabel('epoch')
        loss_ax.set_ylabel('loss')
        loss_ax.legend(loc='upper left')

        acc_ax.plot(history.history['accuracy'], 'b', label='train acc')
        acc_ax.plot(history.history['val_accuracy'], 'g', label='val acc')
        acc_ax.set_ylabel('accuracy')
        acc_ax.legend(loc='lower left')

        plt.show()
