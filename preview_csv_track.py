import pandas as pd
import plotly.graph_objects as go

# Load the data from the uploaded CSV file
file_path = './data/20240624162924-04039-data.csv'
data = pd.read_csv(file_path, delimiter=';')

# Extract relevant data for 3D plotting
latitude = data['latitude']
longitude = data['longitude']
altitude = data['altitude (m)']

z_min = altitude.min() - 20  # Adding a buffer
z_max = altitude.max() + 20  # Adding a buffer

# Create a 3D scatter plot with plotly
fig = go.Figure(data=[go.Scatter3d(
    x=longitude,
    y=latitude,
    z=altitude,
    mode='lines+markers',
    marker=dict(
        size=4,
        color=altitude,                # set color to the altitude values
        colorscale='Viridis',          # choose a colorscale
        opacity=0.8
    )
)])

# Update layout for better visualization
fig.update_layout(
    scene=dict(
        xaxis_title='Longitude',
        yaxis_title='Latitude',
        zaxis_title='Altitude (m)',
        zaxis=dict(range=[z_min, z_max])
    ),
    title='Interactive 3D Plot of Track with Elevation Data'
)

# Show the plot
fig.show()
