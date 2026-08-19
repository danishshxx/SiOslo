#!/bin/sh
set -e

ollama serve &
SERVE_PID=$!

echo "Menunggu Ollama server siap..."
until ollama list >/dev/null 2>&1; do
  sleep 1
done
echo "Ollama server siap."

if ! ollama list | grep -q "sioslo-model"; then
  echo "Model sioslo-model belum ada, membuat dari Modelfile..."
  ollama create sioslo-model -f /models/Modelfile
  echo "Model sioslo-model berhasil dibuat."
else
  echo "Model sioslo-model sudah ada, skip create."
fi

wait $SERVE_PID