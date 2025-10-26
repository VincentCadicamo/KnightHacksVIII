docker build -t plotly-map-app .

docker run --rm -p 8050:8050 -v ./data:/app/data plotly-map-app

