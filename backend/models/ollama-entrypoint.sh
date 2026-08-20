#!/bin/sh
set -e

# Jalankan server Ollama di background
ollama serve &
OLLAMA_PID=$!

# Tunggu server siap
sleep 5

# Buat model custom dari Modelfile jika ada
if [ -f /models/Modelfile ]; then
  echo "Membuat model sioslo-model dari Modelfile..."
  ollama create sioslo-model -f /models/Modelfile
fi

wait $OLLAMA_PID