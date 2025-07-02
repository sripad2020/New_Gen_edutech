import numpy as np
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from keras.src.legacy.preprocessing.text import Tokenizer
from keras.api.preprocessing.sequence import pad_sequences
from keras.api.models import Sequential
from keras.api.layers import Dense,LSTM,Flatten,Embedding
from keras.api.utils import to_categorical
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, classification_report, confusion_matrix



import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score,classification_report,confusion_matrix


def load_text(path):
    with open(path, 'r', encoding='utf-8') as file:
        lines = [line.strip().split(';') for line in file]
    texts, labels = zip(*lines)
    return list(texts), list(map(str.strip, labels))


def preprocess_texts(txts):
    stop_words = set(stopwords.words('english'))
    translator = str.maketrans('', '', string.punctuation)
    preprocessed_texts = [
        ' '.join(word for word in word_tokenize(txt.translate(translator)) if word.lower() not in stop_words)
        for txt in txts
    ]
    return np.array(preprocessed_texts)

train_texts,train_labels = load_text('train.txt')
val_texts,val_labels = load_text('val.txt')
test_texts,test_labels = load_text('test.txt')
train_texts_p = preprocess_texts(train_texts)
val_texts_p = preprocess_texts(val_texts)
test_texts_p = preprocess_texts(test_texts)

enc = LabelEncoder()
train_labels_p = enc.fit_transform(train_labels)
val_labels_p = enc.fit_transform(val_labels)
test_labels_p = enc.fit_transform(test_labels)
list_txts = [x.split() for x in train_texts_p]
flattened_txts = [i for j in list_txts for i in j]
num_words = len(set(flattened_txts))

maxlen = max([len(x.split()) for x in train_texts_p])
tokenizer = Tokenizer(num_words=num_words)
tokenizer.fit_on_texts(train_texts_p)

train_seqs = tokenizer.texts_to_sequences(train_texts_p)
val_seqs = tokenizer.texts_to_sequences(val_texts_p)
test_seqs = tokenizer.texts_to_sequences(test_texts_p)

train_pad = pad_sequences(train_seqs,maxlen=maxlen)
val_pad = pad_sequences(val_seqs,maxlen=maxlen)
test_pad = pad_sequences(test_seqs,maxlen=maxlen)

from tensorflow.keras.layers import Input,GRU,Bidirectional

model = Sequential([
    Input(shape=(maxlen,)),
    Embedding(input_dim=num_words, output_dim=100),  # Stacked GRUs
    GRU(32),
    Dense(6, activation='softmax')
])
model.compile(optimizer=tf.keras.optimizers.RMSprop(learning_rate=0.001),loss='sparse_categorical_crossentropy',metrics=['accuracy'])
history = model.fit(train_pad,train_labels_p,epochs=6,validation_data=(val_pad,val_labels_p),shuffle=True,batch_size=16)

y_pred = model.predict(test_pad)
y_pred_classes = np.argmax(y_pred, axis=1)

accuracy = accuracy_score(test_labels_p, y_pred_classes)
precision = precision_score(test_labels_p, y_pred_classes, average='weighted')
recall = recall_score(test_labels_p, y_pred_classes, average='weighted')
f1 = f1_score(test_labels_p, y_pred_classes, average='weighted')
roc_auc = roc_auc_score(test_labels_p, y_pred, multi_class='ovr')
class_report = classification_report(test_labels_p, y_pred_classes, target_names=enc.classes_, output_dict=True)
cm = confusion_matrix(test_labels_p, y_pred_classes)
model.save('text_classification_model.h5')

# Create visualization
plt.figure(figsize=(15, 10))

# 1. Accuracy Plot
plt.subplot(2, 4, 1)
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()

# 2. Loss Plot
plt.subplot(2, 4, 2)
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

# 3. Confusion Matrix
plt.subplot(2, 4, 3)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=enc.classes_, yticklabels=enc.classes_)
plt.title('Confusion Matrix')
plt.xlabel('Predicted')
plt.ylabel('True')

# 4. Metrics Bar Plot
metrics = {
    'Accuracy': accuracy,
    'Precision': precision,
    'Recall': recall,
    'F1-Score': f1,
    'ROC AUC': roc_auc
}
plt.subplot(2, 4, 4)
plt.bar(metrics.keys(), metrics.values())
plt.title('Classification Metrics')
plt.xticks(rotation=45)
plt.ylabel('Score')

# 5. Precision per class
precision_per_class = [class_report[label]['precision'] for label in enc.classes_]
plt.subplot(2, 4, 5)
plt.bar(enc.classes_, precision_per_class)
plt.title('Precision per Class')
plt.xticks(rotation=45)
plt.ylabel('Precision')

# 6. Recall per class
recall_per_class = [class_report[label]['recall'] for label in enc.classes_]
plt.subplot(2, 4, 6)
plt.bar(enc.classes_, recall_per_class)
plt.title('Recall per Class')
plt.xticks(rotation=45)
plt.ylabel('Recall')

# 7. F1-Score per class
f1_per_class = [class_report[label]['f1-score'] for label in enc.classes_]
plt.subplot(2, 4, 7)
plt.bar(enc.classes_, f1_per_class)
plt.title('F1-Score per Class')
plt.xticks(rotation=45)
plt.ylabel('F1-Score')
plt.tight_layout()
plt.savefig('model_evaluation_metrics.png')