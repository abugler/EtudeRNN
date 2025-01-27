from encoding import decoding_to_midi, encoding_to_LSTM, find_beat_matrix
from nylon_rnn import NylonRNN
import numpy as np
import torch
import datetime
import pretty_midi

absolute_path = "C:\\Users\\Andreas Bugler\\Documents\\NylonRNN_BCE\\"
primer_path = "data\\primer.npy"
model_path = "models\\9303279"
output_path = "midi_output\\"

model = NylonRNN(60, 50, n_layers=15)
beats_to_generate = 64

try:
    primer_matrix = np.load(primer_path)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
except FileNotFoundError:
    primer_path = absolute_path + primer_path
    model_path = absolute_path + model_path
    output_path = absolute_path + output_path
    primer_matrix = np.load(primer_path)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))

primer_matrix = primer_matrix.astype(float)
model.eval()
now = datetime.datetime.now()
np.random.seed(int(now.microsecond * now.second ** 2))
# random_row = np.random.randint(0, primer_matrix.shape[1] / 24)
random_row = 0
generated_matrix = np.empty((50, beats_to_generate * 24))
beat_matrix = find_beat_matrix(generated_matrix, 0)
primer_np = np.append(primer_matrix[np.newaxis, :, random_row:random_row+1], beat_matrix[np.newaxis, :, 0:1], axis=1)
primer = torch.from_numpy(primer_np).float()
generated_matrix[:, 0:1] = primer_np[0, 0:50, :]

# init hidden state
hn = torch.zeros(model.n_layers, 1, model.n_hidden)
# init cell state
cn = torch.zeros(model.n_layers, 1, model.n_hidden)
approx_to_zero = np.vectorize(lambda x: 1 if np.random.random() < x else 0)
approx_to_double = np.vectorize(lambda x: 1 if (np.random.random() + np.random.random()) / 2 < x else 0)

model.set_device("cpu")

for i in range(1, (beats_to_generate) * 24 - 1):
    out, hn, cn = model(primer, hn, cn)
    out = out.detach().numpy()
    generated_matrix[0:44, i + 1] = approx_to_zero(out[0, 0:44, -1])
    generated_matrix[44:50, i + 1] = approx_to_zero(out[0, 44:50, -1])
    primer = torch.from_numpy(np.append(generated_matrix[np.newaxis, :, i:i+1], beat_matrix[np.newaxis, :, i:i+1], axis=1)).float()

midi_data = decoding_to_midi(generated_matrix)
midi_data.write(output_path + str(now.date()) + '_' + str(np.random.randint(0, 1e8)) + ".mid")

