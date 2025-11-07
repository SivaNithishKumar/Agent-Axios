import pickle
import os

os.chdir('codebase_faiss_db')
with open('metadata.pkl', 'rb') as f:
    data = pickle.load(f)

print(f'Total files: {len(data)}')
print('\nFirst 10 file paths:')
for i, item in enumerate(data[:10]):
    print(f'{i+1}. {item["file_path"]}')

print('\nSample metadata structure:')
print(data[0])
